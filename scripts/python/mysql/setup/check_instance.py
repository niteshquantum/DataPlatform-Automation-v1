from pathlib import Path
import sys
import socket
import mysql.connector
from mysql.connector import Error as MySQLError

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import load_database_config

config = load_database_config("mysql")

HOST = config["MYSQL_HOST"]
PORT = int(config["MYSQL_PORT"])
DB = config["MYSQL_DB"]
USER = config["MYSQL_USER"]
PASSWORD = config["MYSQL_PASSWORD"]

PROJECT_MYSQL_DIR = ROOT / "databases" / "mysql"
PROJECT_MYSQL_BIN = PROJECT_MYSQL_DIR / "server" / "bin" / "mysqld.exe"
PROJECT_MYSQL_DATA = PROJECT_MYSQL_DIR / "data"


def check():
    result = {
        "SERVER_AVAILABLE": "FALSE",
        "DATABASE_EXISTS": "FALSE",
        "PORT": str(PORT),
        "HOST": HOST,
        "VERSION": "None",
        "ERROR": "None",
        "TCP_OPEN": "FALSE",
        "PROJECT_BINARIES_EXIST": str(PROJECT_MYSQL_BIN.exists()),
        "PROJECT_DATA_EXISTS": str(PROJECT_MYSQL_DATA.exists()),
        "INSTANCE_STATE": "NO_INSTANCE",
    }

    if not PROJECT_MYSQL_BIN.exists():
        result["PROJECT_BINARIES_EXIST"] = "FALSE"
    else:
        result["PROJECT_BINARIES_EXIST"] = "TRUE"

    if not PROJECT_MYSQL_DATA.exists():
        result["PROJECT_DATA_EXISTS"] = "FALSE"
    else:
        result["PROJECT_DATA_EXISTS"] = "TRUE"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    tcp_result = sock.connect_ex((HOST, PORT))
    sock.close()

    if tcp_result != 0:
        result["ERROR"] = f"Port {PORT} is not listening"
        if result["PROJECT_BINARIES_EXIST"] == "TRUE":
            result["INSTANCE_STATE"] = "INSTANCE_INSTALLED_BUT_STOPPED"
        else:
            result["INSTANCE_STATE"] = "NO_INSTANCE"
        return result

    result["TCP_OPEN"] = "TRUE"

    try:
        conn = mysql.connector.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=PASSWORD,
        )
    except MySQLError as e:
        result["ERROR"] = str(e)
        result["INSTANCE_STATE"] = "PORT_OCCUPIED_BY_NON_MYSQL"
        return result

    result["SERVER_AVAILABLE"] = "TRUE"

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        result["VERSION"] = str(cursor.fetchone()[0])

        cursor.execute("SHOW DATABASES LIKE %s", (DB,))
        db_row = cursor.fetchone()
        result["DATABASE_EXISTS"] = "TRUE" if db_row else "FALSE"

        cursor.close()
        conn.close()
    except MySQLError as e:
        result["ERROR"] = str(e)
        if conn.is_connected():
            conn.close()

    result["INSTANCE_STATE"] = "INSTANCE_RUNNING_AND_USABLE"

    return result


if __name__ == "__main__":

    r = check()

    for k, v in r.items():
        print(f"{k}={v}")
