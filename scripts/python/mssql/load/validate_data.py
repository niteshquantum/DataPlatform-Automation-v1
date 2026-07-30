import json
from pathlib import Path

from scripts.python.mssql.setup.db_connection import get_connection, config

ROOT = Path(__file__).resolve().parents[4]

try:

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DB_NAME()")
    database = cursor.fetchone()[0]

    expected_database = config["MSSQL_DB"]

    if database.lower() != expected_database.lower():
        raise Exception(
            f"Expected database '{expected_database}' "
            f"but connected to '{database}'"
        )

    cursor.execute("""
        SELECT local_tcp_port
        FROM sys.dm_exec_connections
        WHERE session_id = @@SPID
    """)
    port = cursor.fetchone()[0]

    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()[0]

    schema_file = (
        ROOT
        / "metadata"
        / "mssql"
        / "schema_registry.json"
    )

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_registry = json.load(f)

    validated_tables = set(schema_registry.keys())

    if not validated_tables:
        raise Exception(
            "No user tables found in schema_registry.json"
        )

    print()
    print("=" * 50)
    print("MSSQL VALIDATION SUCCESS")
    print("=" * 50)
    print(f"Database : {database}")
    print(f"Port     : {port}")
    print(f"Version  : {version}")

    print()
    print("Tables Validated:")

    for table in sorted(validated_tables):

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_CATALOG = DB_NAME()
              AND TABLE_NAME = ?
            """,
            (table,)
        )

        if cursor.fetchone()[0] == 0:
            print(f"[SKIPPED] {table} : table does not exist")
            continue

        cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
        count = cursor.fetchone()[0]

        print(f"[OK] {table:<30} {count} rows")

    print("=" * 50)

    cursor.close()
    conn.close()

except Exception as e:

    print()
    print("=" * 50)
    print("MSSQL VALIDATION FAILED")
    print("=" * 50)
    print(e)
    print("=" * 50)

    exit(1)