import importlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import (
    load_migration_config,
    load_migration_role_config,
)
from scripts.python.migration.initialize import (
    build_effective_config,
    mask_password,
    validate_database_type,
    validate_required_fields,
)

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
    for db_name in ["mssql", "mysql", "postgresql"]:
        db_defaults.update(load_migration_config(db_name))
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


def get_connection(db_type, config, role_prefix):
    prefix = role_prefix
    db_type_upper = db_type.upper()
    module = import_db_module(db_type)

    if db_type_upper == "MSSQL":
        connection_string = (
            f"DRIVER={{{config[f'{prefix}_ODBC_DRIVER']}}};"
            f"SERVER={config[f'{prefix}_HOST']},{config[f'{prefix}_PORT']};"
            f"DATABASE={config[f'{prefix}_DB']};"
            f"UID={config[f'{prefix}_USER']};"
            f"PWD={config[f'{prefix}_PASSWORD']};"
            "Encrypt=no;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=30;"
        )
        return module.connect(connection_string)

    elif db_type_upper == "MYSQL":
        return module.connect(
            host=config[f"{prefix}_HOST"],
            port=int(config[f"{prefix}_PORT"]),
            user=config[f"{prefix}_USER"],
            password=config[f"{prefix}_PASSWORD"],
            database=config[f"{prefix}_DB"],
        )

    elif db_type_upper == "POSTGRESQL":
        return module.connect(
            host=config[f"{prefix}_HOST"],
            port=int(config[f"{prefix}_PORT"]),
            user=config[f"{prefix}_USER"],
            password=config[f"{prefix}_PASSWORD"],
            database=config[f"{prefix}_DB"],
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
    conn = get_connection(db_type, config, role_prefix)
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
    role = "SOURCE"

    try:
        source_defaults = load_migration_role_config("source")
        db_defaults = load_db_defaults()

        source_effective = build_effective_config(source_defaults, db_defaults, "SOURCE")
        add_extra_fields(source_effective, db_defaults, "SOURCE", source_effective.get("SOURCE_DATABASE", ""))

        db_type = source_effective.get("SOURCE_DATABASE", "")

        valid, msg = validate_database_type(db_type)
        if not valid:
            print(f"ERROR: {msg}")
            return 1

        valid, msg = validate_required_fields(source_effective, "SOURCE")
        if not valid:
            print(f"ERROR: {msg}")
            return 1

        print_validation_summary(role, source_effective)

        test_connection(db_type, source_effective, role)
        print(f"Connection: PASS")

        database = verify_database(db_type, source_effective, role)
        print(f"Database : PASS (verified: {database})")

        schema_ok = verify_schema(db_type, source_effective, role)
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
