#!/usr/bin/env python

"""
Schema Extractor Script

Connects to the database, reads table and column metadata,
and maintains metadata in metadata/schema_registry.json
"""
import sys
import json
import logging
from pathlib import Path

from scripts.python.common.config_loader import load_source_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def detect_schema_changes(existing_columns, current_columns):
    """
    Compare existing and current schema.
    Returns NEW, CHANGED, DELETED or UNCHANGED.
    """

    existing = {c.lower().strip() for c in existing_columns}
    current = {c.lower().strip() for c in current_columns}

    added = list(current - existing)
    deleted = list(existing - current)

    if not existing_columns:
        return {
            "status": "NEW",
            "added_columns": current_columns,
            "deleted_columns": []
        }

    if added:
        return {
            "status": "CHANGED",
            "added_columns": added,
            "deleted_columns": deleted
        }

    if deleted:
        return {
            "status": "DELETED",
            "added_columns": [],
            "deleted_columns": deleted
        }

    return {
        "status": "UNCHANGED",
        "added_columns": [],
        "deleted_columns": []
    }


def update_schema_registry(table_name, columns, registry_path):
    """
    Update schema_registry.json with new columns.
    """
    try:
        if registry_path.exists():
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
        else:
            registry = {}

        # Normalize incoming columns
        columns = [
            col.replace('\ufeff', '').strip()
            for col in columns
        ]

        if table_name in registry:

            existing_columns = [
                col.replace('\ufeff', '').strip()
                for col in registry[table_name]
            ]

            new_columns = []
            seen = set()

            for col in existing_columns + columns:
                key = col.lower()

                if key not in seen:
                    seen.add(key)
                    new_columns.append(col)

            added_columns = [
                col for col in new_columns
                if col not in existing_columns
            ]

            registry[table_name] = new_columns


            logger.info(
                f"Updated table '{table_name}' "
                f"with new columns: {added_columns}"
            )

        else:
            registry[table_name] = columns

            logger.info(
                f"Created new table '{table_name}' "
                f"with columns: {columns}"
            )

        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)

    except Exception as e:
        logger.error(f"Error updating schema registry: {e}")


def get_mysql_tables(conn):
    """
    Get list of user tables from MySQL database.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()")
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables


def get_mysql_columns(conn, table_name):
    """
    Get ordered column names for a MySQL table.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION",
        (table_name,)
    )
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return columns


def get_mssql_tables(conn):
    """
    Get list of user tables from MSSQL database.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_CATALOG = DB_NAME() AND TABLE_TYPE = 'BASE TABLE'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables


def get_mssql_columns(conn, table_name):
    """
    Get ordered column names for an MSSQL table.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_CATALOG = DB_NAME() AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
        (table_name,)
    )
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return columns


def get_postgresql_tables(conn):
    """
    Get list of base tables from PostgreSQL 'public' schema.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = 'public' AND TABLE_TYPE = 'BASE TABLE'"
    )
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables


def get_postgresql_columns(conn, table_name):
    """
    Get ordered column names for a PostgreSQL table in 'public' schema.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COLUMN_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = 'public' AND TABLE_NAME = %s ORDER BY ORDINAL_POSITION",
        (table_name,)
    )
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return columns


def get_source_connection(source_config):
    """
    Returns a connection to the source database using source.conf.
    """
    db_type = source_config.get("SOURCE_DB_TYPE", "").lower()

    if db_type == "mssql":
        import pyodbc
        connection_string = (
            f"DRIVER={{{source_config['SOURCE_ODBC_DRIVER']}}};"
            f"SERVER={source_config['SOURCE_HOST']},{source_config['SOURCE_PORT']};"
            f"DATABASE={source_config['SOURCE_DB']};"
            f"UID={source_config['SOURCE_USER']};"
            f"PWD={source_config['SOURCE_PASSWORD']};"
            "Encrypt=no;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=30;"
        )
        return pyodbc.connect(connection_string)

    elif db_type == "mysql":
        import mysql.connector
        return mysql.connector.connect(
            host=source_config["SOURCE_HOST"],
            port=int(source_config["SOURCE_PORT"]),
            user=source_config["SOURCE_USER"],
            password=source_config["SOURCE_PASSWORD"],
            database=source_config["SOURCE_DB"]
        )

    elif db_type == "postgresql":
        import psycopg2
        return psycopg2.connect(
            host=source_config["SOURCE_HOST"],
            port=int(source_config["SOURCE_PORT"]),
            user=source_config["SOURCE_USER"],
            password=source_config["SOURCE_PASSWORD"],
            database=source_config["SOURCE_DB"]
        )

    else:
        raise ValueError(f"Unsupported source database type: {db_type}")


def main():
    """
    Main function to extract schema from database and update schema registry.
    """
    logger.info("Starting schema extraction...")

    # Define paths
    project_root = Path(__file__).parent.parent

    # Database type from command line
    db_type = sys.argv[1].lower() if len(sys.argv) > 1 else "mysql"

    registry_path = (
        project_root
        / "metadata"
        / db_type
        / "schema_registry.json"
    )

    cdc_path = (
        project_root
        / "metadata"
        / db_type
        / "cdc_status.json"
    )

    logger.info(f"Target database type: {db_type}")

    source_config = load_source_config()
    source_db_type = source_config.get("SOURCE_DB_TYPE", "").lower()

    logger.info(f"Source database type: {source_db_type}")

    if source_db_type not in ("mysql", "mssql", "postgresql"):
        logger.error(f"Unsupported source database type: {source_db_type}")
        return

    # Add project root to path for imports
    sys.path.insert(0, str(project_root))

    try:
        conn = get_source_connection(source_config)
    except Exception as e:
        logger.error(f"Failed to connect to source {source_db_type}: {e}")
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        cdc_status = {"tables": {}}
        cdc_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cdc_path, "w", encoding="utf-8") as f:
            json.dump(cdc_status, f, indent=4)
        logger.info(f"Initialized empty schema registry at {registry_path}")
        logger.info(f"CDC metadata written to {cdc_path}")
        return

    logger.info(f"Connected to source {source_db_type} successfully")
    cdc_status = {"tables": {}}

    try:
        if source_db_type == "mysql":
            tables = get_mysql_tables(conn)
        elif source_db_type == "postgresql":
            tables = get_postgresql_tables(conn)
        else:
            tables = get_mssql_tables(conn)

        logger.info(f"Found {len(tables)} table(s) in source database")

        for table_name in tables:
            normalized_table_name = (
                table_name
                .strip()
                .lower()
                .replace(' ', '_')
            )

            if source_db_type == "mysql":
                columns = get_mysql_columns(conn, table_name)
            elif source_db_type == "postgresql":
                columns = get_postgresql_columns(conn, table_name)
            else:
                columns = get_mssql_columns(conn, table_name)

            if not columns:
                logger.warning(f"No columns found for table: {table_name}")
                continue

            logger.info(f"Extracted columns from {table_name}: {columns}")

            existing_columns = []

            if registry_path.exists():
                with open(registry_path, "r", encoding="utf-8") as f:
                    registry = json.load(f)

                existing_columns = registry.get(normalized_table_name, [])

                result = detect_schema_changes(existing_columns, columns)

                logger.info(
                    f"CDC Status [{normalized_table_name}] : {result['status']}"
                )

                cdc_status["tables"][normalized_table_name] = result

            update_schema_registry(normalized_table_name, columns, registry_path)

    except Exception as e:
        logger.error(f"Error during schema extraction: {e}")
    finally:
        conn.close()

    cdc_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cdc_path, "w", encoding="utf-8") as f:
        json.dump(cdc_status, f, indent=4)

    logger.info(f"CDC metadata written to {cdc_path}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        raise
