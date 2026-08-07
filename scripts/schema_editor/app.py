from flask import Flask, render_template, request
import json
from pathlib import Path

import webbrowser
import threading
import webbrowser
import os

app = Flask(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

import sys

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

    return render_template("index.html", data=data)

@app.route("/save", methods=["POST"])
def save():

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    for key, value in request.form.items():

        table, column = key.split("__")

        data[table][column]["selected_type"] = value

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    threading.Timer(
        1,
        lambda: os._exit(0)
    ).start()

    return """
    <!DOCTYPE html>

    <html>

    <head>

    <meta http-equiv="refresh" content="1">

    </head>

    <body>

    <h2>Schema Saved Successfully ✅</h2>

    <h3>Pipeline will continue automatically...</h3>

    </body>

    </html>
    """

server = None


def shutdown_server():
    global server
    if server:
        server.shutdown()

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":

    #threading.Timer(1, open_browser).start()
    import socket

    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)

    print("\n" + "=" * 60)
    print("ACTION REQUIRED")
    print("=" * 60)
    print(f"Schema Editor is ready.")
    print(f"Open the following URL:")
    print(f"http://{ip}:5000")
    print("")
    print("After clicking 'Save & Continue',")
    print("the Jenkins pipeline will continue automatically.")
    print("=" * 60 + "\n")
    app.run(
    host="0.0.0.0",
    port=5000,
    debug=False,
    use_reloader=False
)