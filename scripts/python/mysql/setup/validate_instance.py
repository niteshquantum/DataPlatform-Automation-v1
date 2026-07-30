from pathlib import Path
import sys
import mysql.connector
from mysql.connector import Error as MySQLError

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import load_database_config

config = load_database_config("mysql")

HOST = config["MYSQL_HOST"]
PORT = int(config["MYSQL_PORT"])
USER = config["MYSQL_USER"]
PASSWORD = config["MYSQL_PASSWORD"]

try:
    conn = mysql.connector.connect(
        host=HOST,
        port=PORT,
        user=USER,
        password=PASSWORD,
    )
    cursor = conn.cursor()
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]
    cursor.execute("SELECT @@port")
    actual_port = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    print()
    print("=" * 50)
    print("MYSQL INSTANCE VALIDATION SUCCESS")
    print("=" * 50)
    print(f"Host    : {HOST}")
    print(f"Port    : {actual_port}")
    print(f"Version : {version}")
    print("=" * 50)

except MySQLError as e:
    print()
    print("=" * 50)
    print("MYSQL INSTANCE VALIDATION FAILED")
    print("=" * 50)
    print(e)
    print("=" * 50)
    exit(1)
