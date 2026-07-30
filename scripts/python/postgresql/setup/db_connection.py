from pathlib import Path
import sys

import psycopg2

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import load_database_config

config = load_database_config("postgresql")


def get_connection(database=None):
    return psycopg2.connect(
        host=config["POSTGRESQL_HOST"],
        port=int(config["POSTGRESQL_PORT"]),
        user=config["POSTGRESQL_USER"],
        password=config["POSTGRESQL_PASSWORD"],
        database=database if database else config["POSTGRESQL_DB"]
    )