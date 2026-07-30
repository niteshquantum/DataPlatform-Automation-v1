
from pymongo import MongoClient
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.mongodb.setup.config_loader import load_config
config = load_config()


def get_client():

    uri = (
        f"mongodb://"
        f"{config['MONGODB_HOST']}:"
        f"{config['MONGODB_PORT']}"
    )

    return MongoClient(uri)

def get_db():

    client = get_client()

    return client[config["MONGODB_DATABASE"]]