import re
from pathlib import Path

from scripts.python.common.config_loader import load_database_config

TABLE_PATTERN = re.compile(r'tableName="([^"]+)"', re.IGNORECASE)
COLUMN_PATTERN = re.compile(r'<column[^>]+name="([^"]+)"', re.IGNORECASE)
CHANGESET_ID_PATTERN = re.compile(r'<changeSet[^>]+id="([^"]+)"', re.IGNORECASE)
CHANGESET_AUTHOR_PATTERN = re.compile(r'<changeSet[^>]+author="([^"]+)"', re.IGNORECASE)
NUMERIC_PREFIX_PATTERN = re.compile(r'^(\d{3})_')


def parse_liquibase_file(file_path):
    """Parse a Liquibase XML file and collect metadata for generator decisions."""
    content = file_path.read_text(encoding="utf-8")
    table_match = TABLE_PATTERN.search(content)
    if not table_match:
        return None

    change_id_match = CHANGESET_ID_PATTERN.search(content)
    author_match = CHANGESET_AUTHOR_PATTERN.search(content)
    columns = {c.lower() for c in COLUMN_PATTERN.findall(content)}

    return {
        "path": file_path,
        "file_name": file_path.name,
        "table_name": table_match.group(1).lower(),
        "columns": columns,
        "change_id": change_id_match.group(1) if change_id_match else None,
        "author": author_match.group(1) if author_match else None,
    }


def collect_existing_change_files(liquibase_dir, exclude_names=None):
    """Collect parsed Liquibase change files under a directory."""
    exclude_names = set(exclude_names or [])
    results = []

    for file_path in sorted(liquibase_dir.glob("*.xml")):
        if file_path.name in exclude_names:
            continue
        parsed = parse_liquibase_file(file_path)
        if parsed:
            results.append(parsed)

    return results


def get_next_change_number(file_paths):
    """Return the next available three-digit change number based on existing file names."""
    max_number = 0
    for file_path in file_paths:
        match = NUMERIC_PREFIX_PATTERN.match(file_path.name)
        if match:
            max_number = max(max_number, int(match.group(1)))
    return max_number + 1


def get_database_applied_changesets(db_type):
    """Return a set of applied Liquibase filenames from DATABASECHANGELOG."""
    config = load_database_config(db_type)
    if not config:
        return []

    applied = []
    try:
        if db_type == "mysql":
            import mysql.connector

            conn = mysql.connector.connect(
                host=config.get("MYSQL_HOST", "localhost"),
                port=int(config.get("MYSQL_PORT", 3306)),
                user=config["MYSQL_USER"],
                password=config.get("MYSQL_PASSWORD", ""),
                database=config["MYSQL_DB"],
            )
        elif db_type == "mssql":
            import pyodbc

            server = config.get("MSSQL_HOST", "localhost")
            port = config.get("MSSQL_PORT", "1433")
            database = config["MSSQL_DB"]
            user = config["MSSQL_USER"]
            password = config.get("MSSQL_PASSWORD", "")
            driver = config.get("MSSQL_ODBC_DRIVER", "ODBC Driver 17 for SQL Server")

            conn_str = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server},{port};"
                f"DATABASE={database};"
                f"UID={user};"
                f"PWD={password};"
                "Encrypt=yes;TrustServerCertificate=yes;"
            )
            conn = pyodbc.connect(conn_str)
        elif db_type == "postgresql":
            import psycopg2

            conn = psycopg2.connect(
                host=config.get("POSTGRESQL_HOST", "localhost"),
                port=config.get("POSTGRESQL_PORT", 5432),
                dbname=config["POSTGRESQL_DB"],
                user=config["POSTGRESQL_USER"],
                password=config.get("POSTGRESQL_PASSWORD", ""),
            )
        else:
            return []

        cursor = conn.cursor()
        cursor.execute("SELECT id, author, filename FROM DATABASECHANGELOG")
        for row in cursor.fetchall():
            filename = row[2] if len(row) > 2 else None
            if filename:
                applied.append(
                    {
                        "id": str(row[0]),
                        "author": str(row[1]),
                        "filename": Path(filename).name,
                    }
                )
        cursor.close()
        conn.close()

    except Exception:
        # Database state may not be available during first run.
        # Generator will still preserve local files and avoid rewriting applied files.
        pass

    return applied


def get_applied_filename_set(applied_changesets):
    return {entry["filename"] for entry in applied_changesets if entry.get("filename")}


def get_applied_id_author_set(applied_changesets):
    return {(entry["id"], entry["author"]) for entry in applied_changesets if entry.get("id") and entry.get("author")}


def load_master_include_order(master_xml_path, namespace):
    import xml.etree.ElementTree as ET

    if not master_xml_path.exists():
        return []

    ET.register_namespace("", namespace)
    tree = ET.parse(master_xml_path)
    root = tree.getroot()
    include_order = []
    for include_elem in root.findall(f"{{{namespace}}}include"):
        filename = include_elem.get("file")
        if filename:
            include_order.append(Path(filename).name)
    return include_order


def build_master_include_order(existing_order, xml_files):
    ordered = [name for name in existing_order if name in xml_files]
    ordered += [name for name in xml_files if name not in ordered]
    return ordered
