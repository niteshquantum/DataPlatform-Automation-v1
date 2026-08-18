
from flask import Flask, render_template, request
import json
from pathlib import Path
import webbrowser
import threading
import os
import sys
import socket
import configparser
import platform
import re
import subprocess
import time
import urllib.request

app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BIND_HOST = "0.0.0.0"
DEFAULT_SCHEMA_EDITOR_PORT = 5000

DATABASE = (
    sys.argv[1].lower()
    if len(sys.argv) > 1
    else "postgresql"
)

DATA_FILE = (
    PROJECT_ROOT
    / "metadata"
    / DATABASE
    / "datatype_registry.json"
)


def is_valid_ipv4(value):
    if not value:
        return False
    try:
        pieces = value.split(".")
        if len(pieces) != 4:
            return False
        for piece in pieces:
            if not piece.isdigit():
                return False
            number = int(piece)
            if number < 0 or number > 255:
                return False
        return True
    except ValueError:
        return False


def is_virtual_interface_name(name):
    if not name:
        return False
    lowered = name.lower()
    virtual_markers = (
        "docker", "veth", "br-", "bridge", "vboxnet", "virbr",
        "hyper-v", "wsl", "loopback", "lo", "default switch",
        "virtual", "vmnet", "container", "podman", "cni", "flannel",
        "tun", "tap", "kube", "kind"
    )
    return any(marker in lowered for marker in virtual_markers)


def build_schema_editor_url(host, port):
    return f"http://{host}:{port}"


def get_schema_editor_port():
    env_port = os.environ.get("SCHEMA_EDITOR_PORT")
    if env_port and env_port.strip():
        try:
            return int(env_port)
        except ValueError:
            pass

    network_conf = PROJECT_ROOT / "config" / "common" / "network.conf"
    if network_conf.exists():
        try:
            config = configparser.ConfigParser()
            config.read(network_conf, encoding="utf-8")
            port_value = config["DEFAULT"].get("SCHEMA_EDITOR_PORT", str(DEFAULT_SCHEMA_EDITOR_PORT))
            if port_value and port_value.strip():
                return int(port_value)
        except (configparser.Error, ValueError, TypeError):
            pass

    return int(DEFAULT_SCHEMA_EDITOR_PORT)


def build_firewall_rule_name(port):
    return f"Schema Editor Port {port} (LAN)"


def windows_firewall_rule_matches_profile(rule, port):
    if not isinstance(rule, dict):
        return False
    local_port = str(rule.get("local_port", "")).strip()
    profiles = rule.get("profiles", [])
    enabled = bool(rule.get("enabled", False))
    return enabled and local_port == str(port) and any(profile.lower() in {"private", "domain"} for profile in profiles)


def parse_linux_default_route_ip(route_output):
    if not route_output:
        return None

    default_route_lines = []
    for line in route_output.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        lower = cleaned.lower()
        if "default" in lower or "0.0.0.0" in lower:
            default_route_lines.append(cleaned)

    for line in default_route_lines:
        dev_match = re.search(r"\bdev\s+(\S+)", line, re.IGNORECASE)
        if not dev_match:
            continue
        dev = dev_match.group(1)
        if is_virtual_interface_name(dev):
            continue
        src_match = re.search(r"\bsrc\s+(\d+\.\d+\.\d+\.\d+)", line, re.IGNORECASE)
        if not src_match:
            continue
        ip = src_match.group(1)
        if is_valid_ipv4(ip) and not ip.startswith("127."):
            return ip

    if default_route_lines:
        return None

    for line in route_output.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        src_match = re.search(r"\bsrc\s+(\d+\.\d+\.\d+\.\d+)", cleaned, re.IGNORECASE)
        if not src_match:
            continue
        ip = src_match.group(1)
        if is_valid_ipv4(ip) and not ip.startswith("127."):
            return ip
    return None


def select_preferred_ip_from_windows_output(output):
    if not output:
        return None

    iface_ip_map = {}
    current_index = None
    default_route_index = None

    route_block = ""
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith("destinationprefix") and "0.0.0.0/0" in line.lower():
            route_block = line
            continue
        if route_block and line.lower().startswith("destinationprefix"):
            route_block = ""
        if route_block:
            route_block += "\n" + line
            if line.lower().startswith("interfaceindex"):
                try:
                    default_route_index = int(line.split(":", 1)[1].strip())
                except ValueError:
                    default_route_index = None
                route_block = ""
                continue

    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.lower().startswith("interfaceindex"):
            try:
                current_index = int(line.split(":", 1)[1].strip())
            except ValueError:
                current_index = None
            continue
        if line.lower().startswith("ipaddress"):
            ip_value = line.split(":", 1)[1].strip()
            if current_index is not None and is_valid_ipv4(ip_value):
                iface_ip_map[current_index] = ip_value

    if default_route_index is not None and default_route_index in iface_ip_map:
        return iface_ip_map[default_route_index]

    for _, ip_value in sorted(iface_ip_map.items()):
        if not ip_value.startswith("127."):
            return ip_value

    for ip in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", output):
        if is_valid_ipv4(ip) and not ip.startswith("127."):
            return ip
    return None


def resolve_active_host_ip():
    system_name = platform.system().lower()

    if system_name.startswith("windows"):
        try:
            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    "Get-NetRoute -AddressFamily IPv4 | Where-Object { $_.DestinationPrefix -eq '0.0.0.0/0' } | Format-List InterfaceIndex, InterfaceAlias, DestinationPrefix, NextHop; Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -and $_.IPAddress -notmatch '127\\.' } | Format-List InterfaceIndex, InterfaceAlias, IPAddress",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.stdout:
                detected = select_preferred_ip_from_windows_output(result.stdout)
                if detected:
                    return detected
        except OSError:
            pass

    for command in (
        ["ip", "route", "get", "1.1.1.1"],
        ["ip", "route", "show", "default"],
        ["route", "-n"],
    ):
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            if result.stdout:
                detected = parse_linux_default_route_ip(result.stdout)
                if detected:
                    return detected
        except OSError:
            continue

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        host = s.getsockname()[0]
    except OSError:
        host = "127.0.0.1"
    finally:
        s.close()
    return host


def ensure_windows_firewall_access(port):
    rule_name = build_firewall_rule_name(port)
    check = subprocess.run(
        ["netsh", "advfirewall", "firewall", "show", "rule", f"name={rule_name}"],
        capture_output=True,
        text=True,
        check=False,
    )

    if check.returncode == 0 and "No rules match" not in check.stdout.lower():
        return True

    add = subprocess.run(
        [
            "netsh",
            "advfirewall",
            "firewall",
            "add",
            "rule",
            f"name={rule_name}",
            "dir=in",
            "action=allow",
            f"localport={port}",
            "protocol=TCP",
            "profile=Private,Domain",
            "remoteip=LocalSubnet",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    if add.returncode != 0:
        raise RuntimeError(
            "The Jenkins process does not have permission to create the Schema Editor firewall rule. "
            "Run Jenkins as an administrator or grant the service permission to update Windows Firewall."
        )

    return True


def resolve_linux_firewall_tool():
    for command in (("ufw",), ("firewall-cmd",), ("iptables",), ("iptables-save",)):
        try:
            result = subprocess.run([*command, "--help"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return command[0]
        except OSError:
            continue
    return None


def ensure_linux_firewall_access(port):
    tool = resolve_linux_firewall_tool()

    if tool is None:
        print(
            "INFO: Firewall automation is not available on this Linux host; Schema Editor may require an existing firewall policy.",
            file=sys.stderr,
        )
        return False

    if tool == "ufw":
        check = subprocess.run(
            ["ufw", "status", "numbered"],
            capture_output=True,
            text=True,
            check=False,
        )
        if check.returncode == 0 and f"{port}/tcp" in check.stdout:
            return True
        result = subprocess.run(
            ["ufw", "allow", f"{port}/tcp"],
            capture_output=True,
            text=True,
            check=False,
        )
    elif tool == "firewall-cmd":
        check = subprocess.run(
            ["firewall-cmd", "--permanent", "--list-ports"],
            capture_output=True,
            text=True,
            check=False,
        )
        if check.returncode == 0 and f"{port}/tcp" in check.stdout:
            return True
        result = subprocess.run(
            ["firewall-cmd", "--permanent", "--add-port", f"{port}/tcp"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            result = subprocess.run(
                ["firewall-cmd", "--reload"],
                capture_output=True,
                text=True,
                check=False,
            )
    elif tool in {"iptables", "iptables-save"}:
        check = subprocess.run(
            ["iptables", "-C", "INPUT", "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"],
            capture_output=True,
            text=True,
            check=False,
        )
        if check.returncode == 0:
            return True
        result = subprocess.run(
            ["iptables", "-I", "INPUT", "-p", "tcp", "--dport", str(port), "-j", "ACCEPT"],
            capture_output=True,
            text=True,
            check=False,
        )
    else:
        result = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")

    if result.returncode != 0:
        raise RuntimeError(
            f"Firewall automation for port {port} is unavailable on this Linux host. "
            "The environment is not configured to modify the active firewall policy."
        )

    return True


def ensure_schema_editor_network_access(port):
    if platform.system().lower().startswith("windows"):
        return ensure_windows_firewall_access(port)
    return ensure_linux_firewall_access(port)


def verify_local_http(host, port):
    url = build_schema_editor_url(host, port)
    try:
        response = urllib.request.urlopen(url, timeout=5)
        return response.status < 400
    except Exception:
        return False


def wait_for_local_http(host, port, timeout_seconds=25):
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if verify_local_http(host, port):
            return True
        time.sleep(0.5)
    return False


@app.route("/")
def home():
    if not DATA_FILE.exists():
        return f"Datatype registry not found: {DATA_FILE}", 404

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return render_template("index.html", data=data, database=DATABASE)


@app.route("/save", methods=["POST"])
def save():
    # Read current datatype registry
    if not DATA_FILE.exists():
        return f"Datatype registry not found: {DATA_FILE}", 404

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Save user-selected datatypes
    for key, value in request.form.items():
        try:
            table, column = key.split("__", 1)
        except ValueError:
            return f"Invalid field name: {key}", 400

        if table not in data:
            return f"Unknown table: {table}", 400

        if column not in data[table]:
            return f"Unknown column: {table}.{column}", 400

        data[table][column]["selected_type"] = value

    # Persist the updated registry
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

    # IMPORTANT:
    # Do not redirect or refresh /save.
    # Jenkins needs this Python process to terminate after
    # the browser has had enough time to display the success page.
    def exit_after_success_page():
        os._exit(0)

    threading.Timer(
        2.0,
        exit_after_success_page
    ).start()

    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Schema Saved</title>
    </head>
    <body>
        <h2>Schema Saved Successfully ✅</h2>
        <h3>Pipeline will continue automatically...</h3>
    </body>
    </html>
    """, 200


def get_schema_editor_url():
    port = get_schema_editor_port()
    host = resolve_active_host_ip()
    return host, port


if __name__ == "__main__":
    configured_port = get_schema_editor_port()
    host = resolve_active_host_ip()

    try:
        ensure_schema_editor_network_access(configured_port)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise

    print("\n" + "=" * 60)
    print("Schema Editor started successfully.")
    print("")
    print(f"Host IP: {host}")
    print(f"Port: {configured_port}")
    print("")
    print("Open the following URL:")
    print(build_schema_editor_url(host, configured_port))
    print("=" * 60 + "\n")

    from werkzeug.serving import make_server

    server = make_server(DEFAULT_BIND_HOST, configured_port, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    if not wait_for_local_http("127.0.0.1", configured_port):
        raise RuntimeError(f"Schema Editor did not successfully bind to port {configured_port}.")

    if host and host != "127.0.0.1":
        if not wait_for_local_http(host, configured_port):
            raise RuntimeError(f"Schema Editor is not reachable at {build_schema_editor_url(host, configured_port)}.")

    try:
        thread.join()
    except KeyboardInterrupt:
        server.shutdown()
        thread.join(timeout=5)
        sys.exit(0)