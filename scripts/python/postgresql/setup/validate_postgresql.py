import sys
from pathlib import Path

import psycopg2

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import load_database_config


def validate_postgresql():

    config = load_database_config("postgresql")

    host = config["POSTGRESQL_HOST"]
    port = int(config["POSTGRESQL_PORT"])
    user = config["POSTGRESQL_USER"]
    password = config["POSTGRESQL_PASSWORD"]

    print("=" * 60)
    print("VALIDATING POSTGRESQL INSTANCE")
    print("=" * 60)

    connection = psycopg2.connect(
        host=host,
        port=port,
        database="postgres",
        user=user,
        password=password
    )

    cursor = connection.cursor()
    cursor.execute("SELECT current_database();")
    current_database = cursor.fetchone()[0]

    cursor.execute("SHOW port;")
    current_port = cursor.fetchone()[0]

    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]

    print(f"Database : {current_database}")
    print(f"Port     : {current_port}")
    print(f"Version  : {version}")

    cursor.close()
    connection.close()

    print()
    print("PostgreSQL validation successful.")


if __name__ == "__main__":

    try:
        validate_postgresql()

    except Exception as error:
        print(f"\nERROR : {error}")
        sys.exit(1)