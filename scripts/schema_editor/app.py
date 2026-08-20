from flask import Flask, render_template, request
import json
from pathlib import Path
import webbrowser
import threading
import os
import sys
import socket
import configparser
import subprocess

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

def get_active_lan_ip():
    """
    Detect the active physical LAN/Wi-Fi IPv4 address.

    Ignores loopback, Docker, virtual bridges,
    Tailscale and other virtual interfaces.
    """

    try:

        # WINDOWS
        if sys.platform.startswith("win"):

            command = (
                "Get-NetIPAddress -AddressFamily IPv4 | "
                "Where-Object { "
                "$_.IPAddress -notlike '127.*' -and "
                "$_.InterfaceAlias -notmatch "
                "'Loopback|Docker|vEthernet|Virtual|Tailscale|Bluetooth' "
                "} | "
                "ForEach-Object { "
                "$adapter = Get-NetAdapter "
                "-InterfaceIndex $_.InterfaceIndex "
                "-ErrorAction SilentlyContinue; "
                "if ($adapter.Status -eq 'Up') { "
                "$_.IPAddress "
                "} "
                "}"
            )

            result = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    command
                ],
                capture_output=True,
                text=True,
                check=False
            )

            candidates = [
                ip.strip()
                for ip in result.stdout.splitlines()
                if ip.strip()
            ]

            if candidates:
                return candidates[0]

        # LINUX / UBUNTU
        elif sys.platform.startswith("linux"):

            result = subprocess.run(
                [
                    "ip",
                    "-o",
                    "-4",
                    "addr",
                    "show",
                    "up"
                ],
                capture_output=True,
                text=True,
                check=False
            )

            ignored_prefixes = (
                "lo",
                "docker",
                "br-",
                "virbr",
                "veth",
                "tailscale",
            )

            for line in result.stdout.splitlines():

                parts = line.split()

                if len(parts) < 4:
                    continue

                interface = parts[1]

                if interface.startswith(ignored_prefixes):
                    continue

                if parts[2] != "inet":
                    continue

                ip = parts[3].split("/")[0]

                if not ip.startswith("127."):
                    return ip

    except Exception as exc:

        print(
            f"WARNING: Failed to detect active LAN IP: {exc}",
            file=sys.stderr
        )

    # Final fallback
    try:

        s = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM
        )

        try:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]

        finally:
            s.close()

    except Exception:
        return "127.0.0.1"
def get_schema_editor_url():
    """
    Determine the URL displayed to the user.

    Priority:
    1. SCHEMA_EDITOR_HOST from environment variable
    2. SCHEMA_EDITOR_HOST from network.conf
    3. Automatically detected active LAN/Wi-Fi IPv4
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

    configured_host = os.environ.get(
        "SCHEMA_EDITOR_HOST",
        ""
    ).strip()

    if network_conf.exists():

        try:

            config = configparser.ConfigParser()

            config.read(
                network_conf,
                encoding="utf-8"
            )

            port = int(
                os.environ.get(
                    "SCHEMA_EDITOR_PORT",
                    config["DEFAULT"].get(
                        "SCHEMA_EDITOR_PORT",
                        port
                    )
                )
            )

            if not configured_host:
                configured_host = (
                    config["DEFAULT"].get(
                        "SCHEMA_EDITOR_HOST",
                        ""
                    ).strip()
                )

        except configparser.Error as exc:

            print(
                f"ERROR: Failed to parse {network_conf}: {exc}",
                file=sys.stderr
            )
            sys.exit(1)

        except Exception as exc:

            print(
                f"ERROR: Failed to load {network_conf}: {exc}",
                file=sys.stderr
            )
            sys.exit(1)

    if configured_host:

        return configured_host, port

    return get_active_lan_ip(), port

if __name__ == "__main__":

    # Get configured port
    _, display_port = get_schema_editor_url()

    # Automatically detect current machine's LAN IP
    network_ip = get_active_lan_ip()

    print("\n" + "=" * 70)
    print("ACTION REQUIRED - SCHEMA EDITOR")
    print("=" * 70)

    print("\nSchema Editor is ready.\n")

    print("1. SAME UBUNTU / JENKINS MACHINE:")
    print(f"   http://127.0.0.1:{display_port}")

    print("\n2. ANOTHER WINDOWS / LAPTOP MACHINE:")
    print(f"   http://{network_ip}:{display_port}")

    print("\nNOTE:")
    print("Use the second link from another machine on the same network.")

    print("\nAfter clicking 'Save & Continue',")
    print("the schema will be saved and the Jenkins pipeline")
    print("will continue automatically.")

    print("=" * 70 + "\n")

    app.run(
        host="0.0.0.0",
        port=display_port,
        debug=False,
        use_reloader=False
    )