import os
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import (
    get_migration_config_path,
    load_migration_config,
    load_migration_role_config,
)
from scripts.python.migration.initialize import (
    build_effective_config,
)


def load_db_defaults():
    db_defaults = {}
    for db_name in ["mssql", "mysql", "postgresql"]:
        db_defaults.update(load_migration_config(db_name))
    return db_defaults


def add_extra_fields(effective_config, db_defaults, role_prefix, db_type):
    db_type_upper = db_type.upper()
    prefix = role_prefix
    extra_fields = {
        "MSSQL": ["ODBC_DRIVER"],
        "MYSQL": [],
        "POSTGRESQL": [],
    }
    for field in extra_fields.get(db_type_upper, []):
        db_key = f"{db_type_upper}_{field}"
        role_key = f"{prefix}_{field}"
        if db_key in db_defaults and role_key not in effective_config:
            effective_config[role_key] = db_defaults[db_key]


def build_effective_source_config():
    source_defaults = load_migration_role_config("source")
    db_defaults = load_db_defaults()
    source_effective = build_effective_config(source_defaults, db_defaults, "SOURCE")
    add_extra_fields(source_effective, db_defaults, "SOURCE", source_effective.get("SOURCE_DATABASE", ""))
    return source_effective


def write_temp_source_conf(effective_config):
    source_conf_path = get_migration_config_path("source")
    backup_path = source_conf_path.with_suffix(".conf.bak")
    original_content = source_conf_path.read_text(encoding="utf-8") if source_conf_path.exists() else ""
    backup_path.write_text(original_content, encoding="utf-8")

    lines = []
    db_type = effective_config.get("SOURCE_DATABASE", "").lower()
    lines.append(f"SOURCE_DB_TYPE={db_type}")

    for key in sorted(effective_config.keys()):
        if key.startswith("SOURCE_") and key != "SOURCE_DATABASE":
            lines.append(f"{key}={effective_config[key]}")

    source_conf_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return backup_path


def restore_source_conf(backup_path):
    source_conf_path = get_migration_config_path("source")
    if backup_path.exists():
        backup_content = backup_path.read_text(encoding="utf-8")
        if backup_content:
            source_conf_path.write_text(backup_content, encoding="utf-8")
        else:
            source_conf_path.unlink(missing_ok=True)
        backup_path.unlink(missing_ok=True)
    else:
        source_conf_path.unlink(missing_ok=True)


def extract_schema(dest_db_type):
    schema_extractor = ROOT / "scripts" / "schema_extractor.py"

    if not schema_extractor.exists():
        print(f"ERROR: Schema extractor not found: {schema_extractor}")
        return 1

    cmd = [
        sys.executable,
        str(schema_extractor),
        dest_db_type.lower(),
    ]

    import subprocess
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode


def print_extraction_summary(dest_db_type):
    registry_path = ROOT / "metadata" / dest_db_type.lower() / "schema_registry.json"
    cdc_path = ROOT / "metadata" / dest_db_type.lower() / "cdc_status.json"

    print()
    print("=" * 48)
    print("EXTRACT SOURCE SCHEMA")
    print("=" * 48)
    print()

    if not registry_path.exists():
        print("ERROR: Schema registry not found")
        return 1

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    table_count = len(registry)
    print(f"Tables Extracted : {table_count}")
    print()

    for table_name, columns in registry.items():
        print(f"Table : {table_name}")
        for col in columns:
            print(f"  - {col}")
        print()

    if cdc_path.exists():
        with open(cdc_path, "r", encoding="utf-8") as f:
            cdc_status = json.load(f)
        changed_tables = [
            t for t, info in cdc_status.get("tables", {}).items()
            if info.get("status") in ("NEW", "CHANGED")
        ]
        print(f"Changed Tables   : {len(changed_tables)}")
        for t in changed_tables:
            print(f"  - {t}")
        print()

    print("EXTRACT SOURCE SCHEMA: PASS")
    print()
    return 0


def main():
    try:
        source_effective = build_effective_source_config()
        source_db_type = source_effective.get("SOURCE_DATABASE", "")

        if not source_db_type:
            print("ERROR: SOURCE_DATABASE is not configured")
            return 1

        dest_defaults = load_migration_role_config("destination")
        db_defaults = load_db_defaults()
        dest_effective = build_effective_config(dest_defaults, db_defaults, "DESTINATION")
        dest_db_type = dest_effective.get("DESTINATION_DATABASE", "")

        if not dest_db_type:
            print("ERROR: DESTINATION_DATABASE is not configured")
            return 1

        print()
        print("=" * 48)
        print("EXTRACT SOURCE SCHEMA")
        print("=" * 48)
        print()
        print(f"Source Database  : {source_db_type}")
        print(f"Target Metadata  : metadata/{dest_db_type.lower()}/")
        print()

        backup_path = None
        try:
            backup_path = write_temp_source_conf(source_effective)
            rc = extract_schema(dest_db_type)
            if rc != 0:
                print("ERROR: Schema extraction failed")
                return rc
        finally:
            if backup_path:
                restore_source_conf(backup_path)

        return print_extraction_summary(dest_db_type)

    except Exception as e:
        print(f"ERROR: Schema extraction failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
