#!/usr/bin/env python
"""
Generic Data Loader

Automatically loads CSV and JSON files from incoming/ into the database using
dynamic schema detection and parameterized inserts.
"""
import hashlib
import csv
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.cdc.metadata_manager import update_file_metadata
from scripts.python.common.config_loader import load_database_config
from scripts.python.mysql.setup.db_connection import get_connection
from scripts.python.common.column_mapper import (
    load_mapping_config,
    resolve_table_mapping,
    get_source_to_target_mapping,
)
from scripts.python.common.datatype_resolver import (
    resolve_column_type,
)


def _load_datatype_registry(db_type):
    datatype_file = ROOT / "metadata" / db_type / "datatype_registry.json"
    if not datatype_file.exists():
        return {}
    try:
        with open(datatype_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _build_column_types(table_name, column_names, db_type, registry):
    if not registry:
        return {}
    types = {}
    for col in column_names:
        try:
            types[col] = resolve_column_type(table_name, col, db_type, registry)
        except Exception:
            types[col] = "VARCHAR(255)"
    return types




try:
    import mysql.connector
except ImportError:
    mysql = None
else:
    mysql = mysql

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None

try:
    import pyodbc
except ImportError:
    pyodbc = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 500
HISTORY_FILE = None


def load_config(config_path):
    config = {}
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        config[key.strip()] = value.strip()
        return config
    except Exception as e:
        logger.error(f"Error reading config file {config_path}: {e}")
        return {}


# def detect_db_type():
#     env_db = os.environ.get('DB_TYPE')
#     if env_db:
#         return env_db.lower()

#     root = Path(__file__).resolve().parent.parent
#     if (root / 'config' / 'mysql.conf').exists():
#         return 'mysql'
#     if (root / 'config' / 'ubuntu' / 'mssql.conf').exists():
#         return 'mssql'
#     if (root / 'config' / 'postgres.conf').exists():
#         return 'postgresql'
#     if (root / 'config' / 'ubuntu' / 'postgres.conf').exists():
#         return 'postgresql'
#     return 'mysql'


def get_database_connection(db_type, config):
    if db_type == 'mysql':
        if mysql is None:
            raise ImportError('mysql.connector is not installed')
        return mysql.connector.connect(
            host=config.get('MYSQL_HOST', 'localhost'),
            port=int(config.get('MYSQL_PORT', 3306)),
            user=config.get('MYSQL_USER', 'root'),
            password=config.get('MYSQL_PASSWORD', ''),
            database=config.get('MYSQL_DB', '')
        )
    if db_type == 'postgresql':
        if psycopg2 is None:
            raise ImportError('psycopg2 is not installed')

        return psycopg2.connect(
            host=config.get('POSTGRESQL_HOST', 'localhost'),
            port=int(config['POSTGRESQL_PORT']),
            user=config.get('POSTGRESQL_USER', 'postgres'),
            password=config.get('POSTGRESQL_PASSWORD', ''),
            dbname=config.get('POSTGRESQL_DB', '')
        )
    if db_type == 'mssql':
        if pyodbc is None:
            raise ImportError('pyodbc is not installed')
        driver = (
            config.get("MSSQL_DRIVER")
            or config.get("MSSQL_ODBC_DRIVER")
            or "ODBC Driver 18 for SQL Server"
        )
        return pyodbc.connect(
            f"DRIVER={{{driver}}};"
            f"SERVER={config.get('MSSQL_HOST', 'localhost')},{config.get('MSSQL_PORT', 1433)};"
            f"DATABASE={config.get('MSSQL_DB', '')};"
            f"UID={config.get('MSSQL_USER', 'sa')};"
            f"PWD={config.get('MSSQL_PASSWORD', '')};"
            f"Encrypt=yes;TrustServerCertificate=yes;"
        )
    raise ValueError(f"Unsupported DB_TYPE: {db_type}")


def quote_name(name, db_type):

    if db_type == 'mysql':
        return '`' + name.replace('`', '``') + '`'

    if db_type == 'postgresql':
        return '"' + name.replace('"', '""') + '"'

    if db_type == 'mssql':
        return '[' + name.replace(']', ']]') + ']'

    return name


def placeholders(db_type, count):
    if db_type == 'mysql' or db_type == 'postgresql':
        return ', '.join(['%s'] * count)
    if db_type == 'mssql':
        return ', '.join(['?'] * count)
    return ', '.join(['%s'] * count)


def get_table_columns(conn, db_type, table_name):
    cursor = conn.cursor()
    try:
        if db_type == 'mysql':
            cursor.execute(
                "SELECT COLUMN_NAME FROM information_schema.columns "
                "WHERE table_schema = DATABASE() AND table_name = %s",
                (table_name,)
            )
            return [row[0] for row in cursor.fetchall()]
        if db_type == 'postgresql':
            cursor.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema = 'public' AND table_name = %s",
                (table_name,)
            )
            return [row[0] for row in cursor.fetchall()]
        if db_type == 'mssql':
            cursor.execute(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ?",
                (table_name,)
            )
            return [row[0] for row in cursor.fetchall()]
    except Exception:
        return []
    finally:
        cursor.close()


def table_exists(conn, db_type, table_name):
    return bool(get_table_columns(conn, db_type, table_name))


def create_table(conn, db_type, table_name, column_names, column_types=None):
    quoted_table = quote_name(table_name, db_type)
    if column_types is None:
        column_types = {}
    columns_sql = ', '.join(
        f"{quote_name(name, db_type)} {column_types.get(name, 'VARCHAR(255)')}"
        for name in column_names
    )
    sql = f"CREATE TABLE {quoted_table} ({columns_sql})"
    cursor = conn.cursor()
    try:
        logger.info(f"Creating table {table_name} with {len(column_names)} column(s)")
        cursor.execute(sql)
        conn.commit()
    finally:
        cursor.close()


def add_missing_columns(conn, db_type, table_name, missing_columns, column_types=None):
    if not missing_columns:
        return

    if column_types is None:
        column_types = {}

    quoted_table = quote_name(table_name, db_type)

    if db_type == "postgresql":
        sql = (
            f"ALTER TABLE {quoted_table} "
            + ", ".join(
                f"ADD COLUMN {quote_name(col, db_type)} {column_types.get(col, 'VARCHAR(255)')}"
                for col in missing_columns
            )
        )
    else:
        definitions = ", ".join(
            f"{quote_name(col, db_type)} {column_types.get(col, 'VARCHAR(255)')}"
            for col in missing_columns
        )

        sql = f"ALTER TABLE {quoted_table} ADD {definitions}"

    cursor = conn.cursor()

    try:
        logger.info(
            f"Adding {len(missing_columns)} missing column(s) to {table_name}"
        )
        logger.info(f"Executing SQL: {sql}")

        cursor.execute(sql)
        conn.commit()

    except Exception:
        conn.rollback()
        raise

    finally:
        cursor.close()


def prepare_rows(rows, actual_columns, file_columns):
    prepared = []
    for row in rows:
        values = [row.get(col) if col in row else None for col in actual_columns]
        prepared.append(values)
    return prepared


def insert_rows(conn, db_type, table_name, actual_columns, rows):
    if not rows:
        return 0
    quoted_table = quote_name(table_name, db_type)
    quoted_columns = ', '.join(quote_name(col, db_type) for col in actual_columns)
    value_placeholders = placeholders(db_type, len(actual_columns))
    sql = f"INSERT INTO {quoted_table} ({quoted_columns}) VALUES ({value_placeholders})"
    cursor = conn.cursor()
    rows_inserted = 0
    try:
        for start in range(0, len(rows), BATCH_SIZE):
            batch = rows[start:start + BATCH_SIZE]
            cursor.executemany(sql, batch)
            rows_inserted += len(batch)
        conn.commit()
    finally:
        cursor.close()
    return rows_inserted


def read_csv_file(path):

    rows = []

    encodings = [
        "utf-8-sig",
        "utf-8",
        "cp1252",
        "latin1"
    ]

    last_error = None

    for encoding in encodings:

        try:

            rows.clear()

            with open(path, "r", encoding=encoding, newline="") as f:

                reader = csv.DictReader(f)

                reader.fieldnames = [
                    h.replace("\ufeff", "").strip()
                    for h in reader.fieldnames
                ]

                for row in reader:

                    rows.append({
                        k.replace("\ufeff", "").strip():
                        (v if v != "" else None)
                        for k, v in row.items()
                    })

            logging.info(f"CSV Encoding Detected : {encoding}")

            return rows

        except UnicodeDecodeError as e:

            last_error = e

            continue

    raise last_error

def read_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
        if not content:
            return []
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            rows = []
            for line in content.splitlines():
                if line.strip():
                    rows.append(json.loads(line))
            return rows
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return [item if isinstance(item, dict) else {} for item in data]
        return []

def get_file_hash(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:

        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)

    return sha256.hexdigest()
def write_history(record):
    path = Path(HISTORY_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(record) + '\n')

def is_file_already_processed(file_path):
    """
    Check if file has already been successfully processed.
    """
    history_path = Path(HISTORY_FILE)
    file_hash = get_file_hash(file_path)
    file_name = file_path.name
    if not history_path.exists():
        return False

    try:
        with open(history_path, 'r', encoding='utf-8') as f:

            for line in f:

                if not line.strip():
                    continue

                try:
                    record = json.loads(line)

                    if (
                        record.get('file') == file_name
                        and record.get('sha256') == file_hash
                        and record.get('status') == 'SUCCESS'):
                        return True

                except json.JSONDecodeError:
                    continue

        return False

    except Exception as e:
        logger.error(f"Error reading history file: {e}")
        return False

def move_file(source_path, dest_dir):
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    target = dest_dir / source_path.name

    if target.exists():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        target = dest_dir / f"{source_path.stem}_{timestamp}{source_path.suffix}"

    source_path.rename(target)

    return target
def write_error_log(file_name, error, failed_dir, db_type):

    failed_dir = Path(failed_dir)
    failed_dir.mkdir(parents=True, exist_ok=True)

    log_file = failed_dir / f"{file_name}.error.log"

    with open(log_file, "w", encoding="utf-8") as f:

        f.write("=" * 60 + "\n")
        f.write("DATA LOAD ERROR\n")
        f.write("=" * 60 + "\n")
        f.write(f"Timestamp : {datetime.now().isoformat()}\n")
        f.write(f"Database  : {db_type}\n")
        f.write(f"File      : {file_name}\n")
        f.write(f"Error     : {str(error)}\n")
        f.write("=" * 60 + "\n")

    logger.info(f"Created error log: {log_file}")

def truncate_table(conn, db_type, table_name):

    quoted_table = quote_name(table_name, db_type)

    cursor = conn.cursor()

    try:

        cursor.execute(f"TRUNCATE TABLE {quoted_table}")

        conn.commit()

        logger.info(f"Truncated table {table_name}")

    finally:

        cursor.close()
def load_and_insert_file(conn, db_type, path, load_mode="skip", strict_schema=False, mapping_config=None):
    if mapping_config is None:
        mapping_config = load_mapping_config()

    table_name = resolve_table_mapping(path.stem, mapping_config)
    logger.info(f"Processing file: {path.name} -> table: {table_name}")

    if path.suffix.lower() == '.csv':
        rows = read_csv_file(path)
    else:
        rows = read_json_file(path)

    if not rows:
        logger.warning(f"No rows found in file {path.name}")
        return 0

    file_columns = []

    for row in rows:
        for key in row.keys():
            if key is not None and key not in file_columns:
                file_columns.append(key)

    source_to_target = get_source_to_target_mapping(file_columns, mapping_config)

    mapped_rows = []
    for row in rows:
        mapped_row = {}
        for src_col, val in row.items():
            if src_col in source_to_target:
                mapped_row[source_to_target[src_col]] = val
        mapped_rows.append(mapped_row)
    rows = mapped_rows

    file_columns = [
        source_to_target[col] for col in file_columns if col in source_to_target
    ]

    if not file_columns:
        logger.warning(f"No columns detected in file {path.name}")
        return 0

    datatype_registry = _load_datatype_registry(db_type)
    column_types = _build_column_types(table_name, file_columns, db_type, datatype_registry)

    existing_columns = get_table_columns(conn, db_type, table_name)
    if existing_columns and load_mode == "reload":
        truncate_table(conn, db_type, table_name)
    if not existing_columns:
        if strict_schema:
            raise Exception(
                f"Strict schema mode: table '{table_name}' does not exist. "
                f"Refusing to create it."
            )
        create_table(conn, db_type, table_name, file_columns, column_types)
        existing_columns = file_columns
    else:
        new_columns = [col for col in file_columns if col not in existing_columns]
        if new_columns:
            if strict_schema:
                raise Exception(
                    f"Strict schema mode: table '{table_name}' has missing columns "
                    f"not present in target schema: {new_columns}"
                )
            new_column_types = {
                col: column_types.get(col, "VARCHAR(255)")
                for col in new_columns
            }
            add_missing_columns(conn, db_type, table_name, new_columns, new_column_types)
            existing_columns.extend(new_columns)

    actual_columns = [col for col in existing_columns if col in file_columns] + \
                     [col for col in existing_columns if col not in file_columns]
    rows_prepared = prepare_rows(rows, actual_columns, file_columns)
    inserted = insert_rows(conn, db_type, table_name, actual_columns, rows_prepared)
    return inserted



def get_config_for_db(db_type):
    return load_database_config(db_type)

def main():
    
    logger.info('Starting generic data loader...')

    project_root = Path(__file__).resolve().parents[1]
    load_mode = os.environ.get("LOAD_MODE", "skip").lower()
    strict_schema = os.environ.get("STRICT_SCHEMA", "false").lower() == "true"
    db_type = sys.argv[1].lower() if len(sys.argv) > 1 else "mysql"

    global HISTORY_FILE

    HISTORY_FILE = (
        project_root
        / 'metadata'
        / db_type
        / 'data_load_history.jsonl'
    )

    mapping_config = load_mapping_config()

    incoming_dir = project_root / "incoming" / db_type
    archive_dir = project_root / "archive" / db_type
    failed_dir = project_root / "failed" / db_type

    logger.info(f"Database type: {db_type}")
    logger.info(f"Incoming directory: {incoming_dir}")

    if not incoming_dir.exists():
        logger.error("incoming/ directory does not exist")
        return

    config = get_config_for_db(db_type)

    if not config:
        logger.error(f"No configuration found for database type {db_type}")
        return

    try:
        conn = get_database_connection(db_type, config)
    except Exception as exc:
        logger.error(f"Unable to connect to database: {exc}")
        return

    data_files = (
        list(incoming_dir.glob("*.csv"))
        + list(incoming_dir.glob("*.json"))
    )

    logger.info(f"Found {len(data_files)} data file(s) in incoming/")

    for path in data_files:

        if load_mode == "skip":

            if is_file_already_processed(path):
                logger.info(f"{path.name} already processed. Skipping.")
                continue

        elif load_mode == "force":

            logger.info(f"{path.name} will be reloaded (FORCE mode).")

        elif load_mode == "reload":

            logger.info(f"{path.name} will be reloaded (RELOAD mode).")

        timestamp = datetime.now().isoformat()
        file_hash = get_file_hash(path)

        rows_inserted = 0
        status = "FAILED"

        try:

            rows_inserted = load_and_insert_file(
                conn,
                db_type,
                path,
                load_mode,
                strict_schema,
                mapping_config
            )

            status = "SUCCESS"

            update_file_metadata(
                path.name,
                {
                    "checksum": file_hash
                }
            )

            move_file(path, archive_dir)

            logger.info(f"Moved {path.name} to archive/")
            logger.info(f"Loaded {rows_inserted} rows from {path.name}")

        except Exception as exc:
            conn.rollback()
            logger.error(f"Error loading file {path.name}: {exc}")

            write_error_log(
                path.name,
                exc,
                failed_dir,
                db_type
            )

            move_file(path, failed_dir)

        finally:

            record = {
                "timestamp": timestamp,
                "file": path.name,
                "sha256": file_hash,
                "table": resolve_table_mapping(path.stem, mapping_config),
                "rows_inserted": rows_inserted,
                "status": status
            }

            write_history(record)

    conn.close()

    logger.info("Data loader completed")
    



if __name__ == "__main__":
    main()
