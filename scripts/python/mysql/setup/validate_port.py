from pathlib import Path
import sys
import socket

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import load_database_config

config = load_database_config("mysql")

host = config["MYSQL_HOST"]
port = int(config["MYSQL_PORT"])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

result = sock.connect_ex((host, port))

sock.close()

if result != 0:

    print()
    print("=" * 50)
    print("PORT VALIDATION FAILED")
    print("=" * 50)
    print(f"Port {port} is not listening")
    print("=" * 50)

    exit(1)

print()
print("=" * 50)
print("PORT VALIDATION SUCCESS")
print("=" * 50)
print(f"Configured Host : {host}")
print(f"Configured Port : {port}")
print("Status          : LISTENING")
print("=" * 50)