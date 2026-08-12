import importlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.python.migration.initialize import (
    load_migration_config,
    build_effective_config,
    mask_password,
    validate_database_type,
    validate_required_fields,
)

MIGRATION_CONFIG_DIR = ROOT / "config" / "windows" / "migration"

SUPPORTED_DATABASES = ["MSSQL", "MYSQL", "POSTGRESQL"]

DB_DRIVER_MAP = {
    "MSSQL": "pyodbc",
    "MYSQL": "mysql.connector",
    "POSTGRESQL": "psycopg2",
}

EXTRA_DB_FIELDS = {
    "MSSQL": ["ODBC_DRIVER"],
    "MYSQL": [],
    "POSTGRESQL": [],
}


def load_db_defaults():
    db_defaults = {}
    for db_file in ["mssql.conf", "mysql.conf", "postgresql.conf"]:
        db_defaults.update(load_migration_config(db_file))
    return db_defaults


def import_db_module(db_type):
    module_name = DB_DRIVER_MAP.get(db_type.upper())
    if not module_name:
        raise ValueError(f"Unsupported database type: {db_type}")
    return importlib.import_module(module_name)


def add_extra_fields(effective_config, db_defaults, role_prefix, db_type):
    db_type_upper = db_type.upper()
    prefix = role_prefix
    extra_fields = EXTRA_DB_FIELDS.get(db_type_upper, [])
    for field in extra_fields:
        db_key = f"{db_type_upper}_{field}"
        role_key = f"{prefix}_{field}"
        if db_key in db_defaults and role_key not in effective_config:
            effective_config[role_key] = db_defaults[db_key]


def get_connection(db_type, config, role_prefix, database=None):
    prefix = role_prefix
    db_type_upper = db_type.upper()
    module = import_db_module(db_type)

    if db_type_upper == "MSSQL":
        target_db = database or config[f"{prefix}_DB"]
        connection_string = (
            f"DRIVER={{{config[f'{prefix}_ODBC_DRIVER']}}};"
            f"SERVER={config[f'{prefix}_HOST']},{config[f'{prefix}_PORT']};"
            f"DATABASE={target_db};"
            f"UID={config[f'{prefix}_USER']};"
            f"PWD={config[f'{prefix}_PASSWORD']};"
            "Encrypt=no;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=30;"
        )
        return module.connect(connection_string)

    elif db_type_upper == "MYSQL":
        conn_kwargs = {
            "host": config[f"{prefix}_HOST"],
            "port": int(config[f"{prefix}_PORT"]),
            "user": config[f"{prefix}_USER"],
            "password": config[f"{prefix}_PASSWORD"],
        }
        if database:
            conn_kwargs["database"] = database
        return module.connect(**conn_kwargs)

    elif db_type_upper == "POSTGRESQL":
        target_db = database or config[f"{prefix}_DB"]
        return module.connect(
            host=config[f"{prefix}_HOST"],
            port=int(config[f"{prefix}_PORT"]),
            user=config[f"{prefix}_USER"],
            password=config[f"{prefix}_PASSWORD"],
            database=target_db,
        )

    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def test_connection(db_type, config, role_prefix):
    conn = get_connection(db_type, config, role_prefix)
    cursor = conn.cursor()
    cursor.execute("SELECT 1")
    cursor.fetchone()
    cursor.close()
    conn.close()


def verify_database(db_type, config, role_prefix):
    prefix = role_prefix
    db_type_upper = db_type.upper()
    conn = get_connection(db_type, config, role_prefix, database=config[f"{prefix}_DB"])
    cursor = conn.cursor()

    try:
        if db_type_upper == "MSSQL":
            cursor.execute("SELECT DB_NAME()")
        elif db_type_upper == "MYSQL":
            cursor.execute("SELECT DATABASE()")
        elif db_type_upper == "POSTGRESQL":
            cursor.execute("SELECT current_database()")
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

        database = cursor.fetchone()[0]
        expected_db = config[f"{prefix}_DB"]
        if database.lower() != expected_db.lower():
            raise Exception(
                f"Expected database '{expected_db}' but connected to '{database}'."
            )
        return database
    finally:
        cursor.close()
        conn.close()


def verify_schema(db_type, config, role_prefix):
    prefix = role_prefix
    schema = config.get(f"{prefix}_SCHEMA", "")
    if not schema:
        return None

    db_type_upper = db_type.upper()
    conn = get_connection(db_type, config, role_prefix)
    cursor = conn.cursor()

    try:
        if db_type_upper == "MSSQL":
            cursor.execute(
                "SELECT name FROM sys.schemas WHERE name = ?",
                (schema,),
            )
            result = cursor.fetchone()
            return result is not None

        elif db_type_upper == "POSTGRESQL":
            cursor.execute(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s",
                (schema,),
            )
            result = cursor.fetchone()
            return result is not None

        elif db_type_upper == "MYSQL":
            return True

        return None
    finally:
        cursor.close()
        conn.close()


def database_exists(db_type, config, role_prefix):
    prefix = role_prefix
    db_type_upper = db_type.upper()
    db_name = config[f"{prefix}_DB"]

    if db_type_upper == "MSSQL":
        conn = get_connection(db_type, config, role_prefix, database="master")
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT name FROM sys.databases WHERE name = ?",
                (db_name,),
            )
            result = cursor.fetchone()
            return result is not None
        finally:
            cursor.close()
            conn.close()

    elif db_type_upper == "MYSQL":
        conn = get_connection(db_type, config, role_prefix)
        cursor = conn.cursor()
        try:
            cursor.execute("SHOW DATABASES")
            for (name,) in cursor.fetchall():
                if name.lower() == db_name.lower():
                    return True
            return False
        finally:
            cursor.close()
            conn.close()

    elif db_type_upper == "POSTGRESQL":
        conn = get_connection(db_type, config, role_prefix, database="postgres")
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT datname FROM pg_database WHERE datname = %s",
                (db_name,),
            )
            result = cursor.fetchone()
            return result is not None
        finally:
            cursor.close()
            conn.close()

    return False


def create_database(db_type, config, role_prefix):
    prefix = role_prefix
    db_type_upper = db_type.upper()
    db_name = config[f"{prefix}_DB"]

    if db_type_upper == "MSSQL":
        conn = get_connection(db_type, config, role_prefix, database="master")
        cursor = conn.cursor()
        try:
            cursor.execute(f"CREATE DATABASE [{db_name}]")
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    elif db_type_upper == "MYSQL":
        conn = get_connection(db_type, config, role_prefix)
        cursor = conn.cursor()
        try:
            cursor.execute(f"CREATE DATABASE `{db_name}`")
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    elif db_type_upper == "POSTGRESQL":
        conn = get_connection(db_type, config, role_prefix, database="postgres")
        cursor = conn.cursor()
        try:
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            conn.commit()
        finally:
            cursor.close()
            conn.close()

    else:
        raise ValueError(f"Unsupported database type: {db_type}")


def print_validation_summary(role, config):
    prefix = role
    db_type = config.get(f"{role}_DATABASE", "").upper()

    print()
    print(f"{role} VALIDATION")
    print("-" * 48)
    print(f"Database : {db_type}")
    print(f"Host     : {config.get(f'{prefix}_HOST', '')}")
    print(f"Port     : {config.get(f'{prefix}_PORT', '')}")
    print(f"DB       : {config.get(f'{prefix}_DB', '')}")
    print(f"Schema   : {config.get(f'{prefix}_SCHEMA', '')}")
    print(f"User     : {config.get(f'{prefix}_USER', '')}")
    print(f"Password : {mask_password(config.get(f'{prefix}_PASSWORD', ''))}")


def main():
    role = "DESTINATION"

    try:
        dest_defaults = load_migration_config("destination.conf")
        db_defaults = load_db_defaults()

        dest_effective = build_effective_config(dest_defaults, db_defaults, "DESTINATION")
        add_extra_fields(dest_effective, db_defaults, "DESTINATION", dest_effective.get("DESTINATION_DATABASE", ""))

        db_type = dest_effective.get("DESTINATION_DATABASE", "")

        valid, msg = validate_database_type(db_type)
        if not valid:
            print(f"ERROR: {msg}")
            return 1

        valid, msg = validate_required_fields(dest_effective, "DESTINATION")
        if not valid:
            print(f"ERROR: {msg}")
            return 1

        print_validation_summary(role, dest_effective)

        test_connection(db_type, dest_effective, role)
        print(f"Connection: PASS")

        if database_exists(db_type, dest_effective, role):
            print(f"Database : PASS (exists)")
        else:
            db_name = dest_effective.get(f"{role}_DB", "")
            print(f"Database {db_name} does not exist")
            print(f"Creating database {db_name}...")
            create_database(db_type, dest_effective, role)
            print(f"Database created successfully")

        database = verify_database(db_type, dest_effective, role)
        print(f"Database : PASS (verified: {database})")

        schema_ok = verify_schema(db_type, dest_effective, role)
        if schema_ok is None:
            print(f"Schema   : (none)")
        elif schema_ok:
            print(f"Schema   : PASS")
        else:
            print(f"Schema   : FAIL")
            return 1

        print()
        print(f"{role} VALIDATION: PASS")
        print()
        return 0

    except Exception as e:
        print(f"ERROR: {role.lower()} validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
