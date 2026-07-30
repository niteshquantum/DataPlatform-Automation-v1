from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

import psycopg2

from db_connection import get_connection
from scripts.python.common.config_loader import load_database_config


def create_database():

    config = load_database_config("postgresql")

    database = config["POSTGRESQL_DB"]
    user = config["POSTGRESQL_USER"]
    password = config["POSTGRESQL_PASSWORD"]
    host = config["POSTGRESQL_HOST"]
    port = int(config["POSTGRESQL_PORT"])

    print("=" * 60)
    print("CREATE POSTGRESQL DATABASE")
    print("=" * 60)
    print(f"Database : {database}")
    print(f"Host     : {host}")
    print(f"Port     : {port}")
    print()

    connection = psycopg2.connect(
        host=host,
        port=port,
        database="postgres",
        user=user,
        password=password
    )

    connection.autocommit = True

    cursor = connection.cursor()

    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s",
        (database,)
    )

    exists = cursor.fetchone()

    if exists:

        print(f"Database already exists : {database}")

    else:

        cursor.execute(f'CREATE DATABASE "{database}"')

        print(f"Database created : {database}")

    cursor.close()
    connection.close()

    print()
    print("Database validation successful.")


if __name__ == "__main__":

    try:

        create_database()

    except Exception as error:

        print(f"\nERROR : {error}")

        sys.exit(1)