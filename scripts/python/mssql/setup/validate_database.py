from pathlib import Path
import sys

# =====================================
# PROJECT ROOT
# =====================================

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

# =====================================
# IMPORTS
# =====================================

from scripts.python.mssql.setup.db_connection import (
    get_connection,
    config,
)

# =====================================
# VALIDATION
# =====================================

try:

    conn = get_connection()
    cursor = conn.cursor()

    # =====================================
    # DATABASE
    # =====================================

    cursor.execute("SELECT DB_NAME()")

    database = cursor.fetchone()[0]

    expected_database = config["MSSQL_DB"]

    if database.lower() != expected_database.lower():

        raise Exception(
            f"Expected database '{expected_database}' but connected to '{database}'."
        )

    # =====================================
    # SERVER NAME
    # =====================================

    cursor.execute("SELECT @@SERVERNAME")

    server_name = cursor.fetchone()[0]

    # =====================================
    # PORT
    # =====================================

    cursor.execute(
        """
        SELECT local_tcp_port
        FROM sys.dm_exec_connections
        WHERE session_id = @@SPID;
        """
    )

    port = int(cursor.fetchone()[0])

    expected_port = int(config["MSSQL_PORT"])

    if port != expected_port:

        raise Exception(
            f"Expected port {expected_port} but connected to {port}."
        )

    # =====================================
    # VERSION
    # =====================================

    cursor.execute("SELECT @@VERSION")

    version = cursor.fetchone()[0]

    expected_major = "16."

    if expected_major not in version:

        raise Exception(
            f"Expected SQL Server 2022 (16.x) but found:\n{version}"
        )

    # =====================================
    # SUCCESS
    # =====================================

    print()
    print("=" * 50)
    print("MSSQL DATABASE VALIDATION SUCCESS")
    print("=" * 50)
    print(f"Server   : {server_name}")
    print(f"Database : {database}")
    print(f"Port     : {port}")
    print(f"Version  : {version.splitlines()[0]}")
    print("=" * 50)
    print()

    cursor.close()
    conn.close()

except Exception as e:

    print()
    print("=" * 50)
    print("MSSQL DATABASE VALIDATION FAILED")
    print("=" * 50)
    print(e)
    print("=" * 50)

    sys.exit(1)