
from flask import Flask, render_template, request
import json
from pathlib import Path
import webbrowser
import threading
import os
import sys
import socket
import configparser

app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

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


def _is_internal_ip(ip):
    parts = ip.split(".")
    if len(parts) != 4:
        return True

    try:
        a, b, c, d = map(int, parts)
    except ValueError:
        return True

    if a == 127:
        return True

    if a == 172 and 16 <= b <= 31:
        return True

    if a == 192 and b == 168 and c == 122:
        return True

    if a == 100 and 64 <= b <= 127:
        return True

    return False


def _get_all_interface_ips():
    ips = set()

    try:
        hostname = socket.gethostname()
        for res in socket.getaddrinfo(hostname, None, family=socket.AF_INET):
            ip = res[4][0]
            if not ip.startswith("127."):
                ips.add(ip)
    except Exception:
        pass

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ips.add(s.getsockname()[0])
        finally:
            s.close()
    except Exception:
        pass

    try:
        import subprocess
        output = subprocess.check_output(
            ["ip", "-4", "addr", "show"],
            text=True,
            stderr=subprocess.DEVNULL
        )
        for line in output.splitlines():
            line = line.strip()
            if line.startswith("inet "):
                parts = line.split()
                if len(parts) >= 2:
                    cidr = parts[1]
                    ip = cidr.split("/")[0]
                    if not ip.startswith("127."):
                        ips.add(ip)
    except Exception:
        pass

    return ips


def _get_external_ip(interface_ips=None):
    if interface_ips is None:
        interface_ips = _get_all_interface_ips()

    candidates = sorted(
        ip for ip in interface_ips if not _is_internal_ip(ip)
    )

    for ip in candidates:
        if ip.startswith("192.168."):
            return ip

    for ip in candidates:
        if ip.startswith("10."):
            return ip

    if candidates:
        return candidates[0]

    return "127.0.0.1"


def get_schema_editor_url():
    """
    Determine the URL that should be displayed to the user.
    The actual Flask port is controlled by SCHEMA_EDITOR_PORT.
    """

    network_conf = (
        PROJECT_ROOT
        / "config"
        / "common"
        / "network.conf"
    )

    port = int(
        os.environ.get(
            "SCHEMA_EDITOR_PORT",
            "5000"
        )
    )

    interface_ips = _get_all_interface_ips()
    host = None

    if network_conf.exists():
        try:
            config = configparser.ConfigParser()
            config.read(network_conf)

            port = int(
                config["DEFAULT"].get(
                    "SCHEMA_EDITOR_PORT",
                    port
                )
            )

            configured_host = config["DEFAULT"].get(
                "JENKINS_HOST",
                ""
            ).strip()

            if configured_host and configured_host in interface_ips:
                host = configured_host
        except Exception:
            pass

    if not host:
        host = _get_external_ip(interface_ips)

    return host, port


if __name__ == "__main__":

    print("\n" + "=" * 60)
    print("ACTION REQUIRED")
    print("=" * 60)
    print("Schema Editor is ready.")
    print("Open the following URL:\n")

    host, display_port = get_schema_editor_url()

    print(f"http://{host}:{display_port}")

    print("")
    print("After clicking 'Save & Continue',")
    print("the schema will be saved and the Jenkins pipeline")
    print("will continue automatically.")
    print("=" * 60 + "\n")

    # The actual Flask binding port is controlled by the
    # environment variable. Default is 5000.
    configured_port = int(
        os.environ.get(
            "SCHEMA_EDITOR_PORT",
            "5000"
        )
    )

    app.run(
        host="0.0.0.0",
        port=configured_port,
        debug=False,
        use_reloader=False
    )