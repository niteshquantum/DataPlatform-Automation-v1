from pathlib import Path
import socket
import sys

# =====================================
# PROJECT ROOT
# =====================================

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

# =====================================
# LOAD CONFIG
# =====================================

from scripts.python.common.config_loader import load_database_config

config = load_database_config("mssql")

host = config["MSSQL_HOST"]
port = int(config["MSSQL_PORT"])

# =====================================
# VALIDATE PORT
# =====================================

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

result = sock.connect_ex((host, port))

sock.close()

if result != 0:

    print()
    print("=" * 50)
    print("MSSQL PORT VALIDATION FAILED")
    print("=" * 50)
    print(f"Host   : {host}")
    print(f"Port   : {port}")
    print("Status : NOT LISTENING")
    print("=" * 50)

    sys.exit(1)

print()
print("=" * 50)
print("MSSQL PORT VALIDATION SUCCESS")
print("=" * 50)
print(f"Host   : {host}")
print(f"Port   : {port}")
print("Status : LISTENING")
print("=" * 50)