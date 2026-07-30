import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import load_database_config


def validate_port():

    config = load_database_config("postgresql")

    host = config["POSTGRESQL_HOST"]
    port = int(config["POSTGRESQL_PORT"])

    print("=" * 60)
    print("VALIDATING POSTGRESQL PORT")
    print("=" * 60)
    print(f"Host : {host}")
    print(f"Port : {port}")
    print()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)

    result = sock.connect_ex((host, port))

    sock.close()

    if result != 0:
        raise Exception(f"Unable to connect to PostgreSQL on {host}:{port}")

    print("PostgreSQL port validation successful.")


if __name__ == "__main__":

    try:

        validate_port()

    except Exception as error:

        print(f"\nERROR : {error}")

        sys.exit(1)