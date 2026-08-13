import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import (
    load_config,
    get_project_root,
    load_migration_config,
    load_migration_role_config,
)

PROJECT_ROOT = get_project_root()

SUPPORTED_DATABASES = ["MSSQL", "MYSQL", "POSTGRESQL"]

DB_FIELD_MAP = {
    "MSSQL": ["HOST", "PORT", "DB", "USER", "PASSWORD", "SCHEMA"],
    "MYSQL": ["HOST", "PORT", "DB", "USER", "PASSWORD", "SCHEMA"],
    "POSTGRESQL": ["HOST", "PORT", "DB", "USER", "PASSWORD", "SCHEMA"],
}


def env_override(config, role_prefix):
    prefix = f"{role_prefix}_"
    for env_key in os.environ:
        if env_key.startswith(prefix):
            value = os.environ[env_key]
            if value:
                config[env_key] = value.strip()
    return config


def map_db_config_to_role(db_config, db_type, role_prefix):
    db_type_upper = db_type.upper()
    if db_type_upper not in DB_FIELD_MAP:
        return {}
    fields = DB_FIELD_MAP[db_type_upper]
    result = {}
    for field in fields:
        db_key = f"{db_type_upper}_{field}"
        role_key = f"{role_prefix}_{field}"
        if db_key in db_config:
            result[role_key] = db_config[db_key]
    return result


def build_effective_config(role_defaults, db_defaults, role_prefix):
    db_type = role_defaults.get(f"{role_prefix}_DATABASE", "")
    env_db = os.environ.get(f"{role_prefix}_DATABASE", "")
    if env_db:
        db_type = env_db.strip()

    mapped_db_defaults = map_db_config_to_role(db_defaults, db_type, role_prefix)
    effective = dict(mapped_db_defaults)
    for key, value in role_defaults.items():
        effective[key] = value
    effective = env_override(effective, role_prefix)
    return effective


def mask_password(password):
    if password is None:
        return ""
    return "*" * len(password)


def validate_database_type(db_type):
    if not db_type:
        return False, "DATABASE type is required"
    if db_type.upper() not in SUPPORTED_DATABASES:
        return False, f"Unsupported DATABASE type: {db_type}. Supported: {', '.join(SUPPORTED_DATABASES)}"
    return True, ""


def validate_required_fields(config, role):
    required = [
        f"{role}_DATABASE",
        f"{role}_HOST",
        f"{role}_PORT",
        f"{role}_DB",
        f"{role}_USER",
    ]
    missing = [field for field in required if not config.get(field)]
    if missing:
        return False, f"Missing required fields for {role}: {', '.join(missing)}"
    return True, ""


def validate_not_same_endpoint(source, dest):
    same_db = source.get("SOURCE_DATABASE", "").upper() == dest.get("DESTINATION_DATABASE", "").upper()
    same_host = source.get("SOURCE_HOST", "") == dest.get("DESTINATION_HOST", "")
    same_port = source.get("SOURCE_PORT", "") == dest.get("DESTINATION_PORT", "")
    same_dbname = source.get("SOURCE_DB", "") == dest.get("DESTINATION_DB", "")
    if same_db and same_host and same_port and same_dbname:
        return False, "Source and destination resolve to the exact same database endpoint and database name"
    return True, ""


def print_summary(source, dest):
    print("=" * 48)
    print("INITIALIZE MIGRATION")
    print("=" * 48)
    print()
    print("SOURCE")
    print("-" * 48)
    print(f"Database : {source.get('SOURCE_DATABASE', '').upper()}")
    print(f"Host     : {source.get('SOURCE_HOST', '')}")
    print(f"Port     : {source.get('SOURCE_PORT', '')}")
    print(f"DB       : {source.get('SOURCE_DB', '')}")
    print(f"Schema   : {source.get('SOURCE_SCHEMA', '')}")
    print(f"User     : {source.get('SOURCE_USER', '')}")
    print(f"Password : {mask_password(source.get('SOURCE_PASSWORD', ''))}")
    print()
    print("DESTINATION")
    print("-" * 48)
    print(f"Database : {dest.get('DESTINATION_DATABASE', '').upper()}")
    print(f"Host     : {dest.get('DESTINATION_HOST', '')}")
    print(f"Port     : {dest.get('DESTINATION_PORT', '')}")
    print(f"DB       : {dest.get('DESTINATION_DB', '')}")
    print(f"Schema   : {dest.get('DESTINATION_SCHEMA', '')}")
    print(f"User     : {dest.get('DESTINATION_USER', '')}")
    print(f"Password : {mask_password(dest.get('DESTINATION_PASSWORD', ''))}")
    print()
    print("MIGRATION INITIALIZATION: PASS")
    print()


def main():
    try:
        source_defaults = load_migration_role_config("source")
        dest_defaults = load_migration_role_config("destination")

        db_defaults = {}
        for db_name in ["mssql", "mysql", "postgresql"]:
            db_defaults.update(load_migration_config(db_name))

        source_effective = build_effective_config(source_defaults, db_defaults, "SOURCE")
        dest_effective = build_effective_config(dest_defaults, db_defaults, "DESTINATION")

        for role, config in [("SOURCE", source_effective), ("DESTINATION", dest_effective)]:
            db_type = config.get(f"{role}_DATABASE", "")
            valid, msg = validate_database_type(db_type)
            if not valid:
                print(f"ERROR: {msg}")
                return 1

        for role, config in [("SOURCE", source_effective), ("DESTINATION", dest_effective)]:
            valid, msg = validate_required_fields(config, role)
            if not valid:
                print(f"ERROR: {msg}")
                return 1

        valid, msg = validate_not_same_endpoint(source_effective, dest_effective)
        if not valid:
            print(f"ERROR: {msg}")
            return 1

        print_summary(source_effective, dest_effective)
        return 0

    except FileNotFoundError as e:
        print(f"ERROR: Configuration file not found: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Migration initialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
