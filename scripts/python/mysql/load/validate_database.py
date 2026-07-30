from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.mysql.setup.db_connection import get_connection, config

try:

    conn = get_connection()
    cursor = conn.cursor()

    # =====================================
    # DATABASE
    # =====================================

    cursor.execute("SELECT DATABASE()")
    database = cursor.fetchone()[0]

    expected_database = config["MYSQL_DB"]

    if database.lower() != expected_database.lower():
        raise Exception(
            f"Expected database '{expected_database}' but connected to '{database}'"
        )

    # =====================================
    # PORT
    # =====================================

    cursor.execute("SELECT @@port")
    port = cursor.fetchone()[0]

    expected_port = int(config["MYSQL_PORT"])

    if port != expected_port:
        raise Exception(
            f"Expected port {expected_port} but connected to {port}"
        )

    # =====================================
    # VERSION
    # =====================================

    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()[0]

    expected_version = config["MYSQL_VERSION"]

    if not version.startswith(expected_version):
        raise Exception(
            f"Expected MySQL {expected_version} but found {version}"
        )

   


    # =====================================
    # SUCCESS
    # =====================================

    print()
    print("=" * 50)
    print("MYSQL DATABASE VALIDATION SUCCESS")
    print("=" * 50)
    print(f"Database : {database}")
    print(f"Port     : {port}")
    print(f"Version  : {version}")
    print()



    cursor.close()
    conn.close()

except Exception as e:

    print()
    print("=" * 50)
    print("MYSQL DATABASE VALIDATION FAILED")
    print("=" * 50)
    print(e)
    print("=" * 50)

    exit(1)
