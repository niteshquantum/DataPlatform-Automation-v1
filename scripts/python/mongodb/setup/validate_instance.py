from pathlib import Path
import sys
from pymongo import MongoClient
from pymongo.errors import PyMongoError

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.mongodb.setup.config_loader import load_config

config = load_config()

HOST = config["MONGODB_HOST"]
PORT = int(config["MONGODB_PORT"])

try:
    client = MongoClient(f"mongodb://{HOST}:{PORT}", serverSelectionTimeoutMS=2000)

    client.admin.command("ping")

    server_info = client.server_info()

    version = server_info.get("version", "Unknown")

    client.close()

    print()
    print("=" * 50)
    print("MONGODB INSTANCE VALIDATION SUCCESS")
    print("=" * 50)
    print(f"Host    : {HOST}")
    print(f"Port    : {PORT}")
    print(f"Version : {version}")
    print(f"Status  : RUNNING AND USABLE")
    print("=" * 50)

except PyMongoError as e:
    print()
    print("=" * 50)
    print("MONGODB INSTANCE VALIDATION FAILED")
    print("=" * 50)
    print(e)
    print("=" * 50)
    exit(1)
