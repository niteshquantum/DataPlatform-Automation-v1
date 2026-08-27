from flask import Flask, render_template, request
import json
from pathlib import Path
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

    return render_template(
        "index.html",
        data=data,
        database=DATABASE
    )


@app.route("/save", methods=["POST"])
def save():

    if not DATA_FILE.exists():
        return f"Datatype registry not found: {DATA_FILE}", 404

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

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

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

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
    Automatically detect the active physical
    LAN / Wi-Fi IPv4 address.

    Ignores Docker, virtual bridges,
    Tailscale, loopback, etc.
    """

    try:

        # ---------------- WINDOWS ----------------
        if sys.platform.startswith("win"):

            command = (
                "Get-NetIPAddress -AddressFamily IPv4 | "
                "Where-Object { "
                "$_.IPAddress -notlike '127.*' -and "
                "$_.InterfaceAlias -notmatch "
                "'Loopback|Docker|vEthernet|Virtual|"
                "Tailscale|Bluetooth' "
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

        # ---------------- LINUX / UBUNTU ----------------
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


def get_schema_editor_config():
    """
    Read fixed Ubuntu/Jenkins machine IP
    and port from network.conf.
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

        except Exception as exc:

            print(
                f"ERROR: Failed to load "
                f"{network_conf}: {exc}",
                file=sys.stderr
            )

            sys.exit(1)

    return configured_host, port


if __name__ == "__main__":

    # Read configured Ubuntu server IP and port
    ubuntu_ip, display_port = get_schema_editor_config()

    # Automatically detect the active LAN/Wi-Fi IP
    # of the machine currently running this application
    active_ip = get_active_lan_ip()

    print("\n" + "=" * 70)
    print("ACTION REQUIRED - SCHEMA EDITOR")
    print("=" * 70)

    print("\nSchema Editor is ready.")
    print("Use the appropriate URL based on where you are accessing it.\n")

    print("1. CURRENT MACHINE - NETWORK ACCESS")
    print(f"   http://{active_ip}:{display_port}")
    print("   Use this URL from another device connected to the same network.\n")

    print("2. SAME MACHINE - LOCAL ACCESS")
    print(f"   http://127.0.0.1:{display_port}")
    print("   Use this URL when accessing the Schema Editor from the machine")
    print("   where the application is currently running.\n")

    if ubuntu_ip:
        print("3. CONFIGURED UBUNTU SERVER - NETWORK ACCESS")
        print(f"   http://{ubuntu_ip}:{display_port}")
        print("   Use this URL to access the configured Ubuntu server.")
        print("   The server address is defined in config/common/network.conf.\n")

    print("After selecting datatypes, click 'Save & Continue'.")
    print("The selections will be saved and the pipeline will continue automatically.")

    print("=" * 70 + "\n")

    app.run(
        host="0.0.0.0",
        port=display_port,
        debug=False,
        use_reloader=False
    )