import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.python.migration.initialize import (
    load_migration_config,
    build_effective_config,
)

MIGRATION_CONFIG_DIR = ROOT / "config" / "windows" / "migration"

EXTRA_DB_FIELDS = {
    "MSSQL": ["ODBC_DRIVER", "DRIVER_VERSION", "INSTANCE", "LIQUIBASE_VERSION"],
    "MYSQL": ["DRIVER_VERSION", "LIQUIBASE_VERSION"],
    "POSTGRESQL": ["DRIVER_VERSION", "LIQUIBASE_VERSION"],
}


def load_db_defaults():
    db_defaults = {}
    for db_file in ["mssql.conf", "mysql.conf", "postgresql.conf"]:
        db_defaults.update(load_migration_config(db_file))
    return db_defaults


def get_destination_config():
    dest_defaults = load_migration_config("destination.conf")
    db_defaults = load_db_defaults()
    dest_effective = build_effective_config(dest_defaults, db_defaults, "DESTINATION")
    return dest_effective, db_defaults


def write_temp_db_config(effective_config, db_defaults, db_type):
    db_type_upper = db_type.upper()
    config_path = ROOT / "config" / "windows" / f"{db_type.lower()}.conf"

    backup_path = config_path.with_suffix(".conf.bak")
    original_content = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
    backup_path.write_text(original_content, encoding="utf-8")

    lines = []
    for key, value in effective_config.items():
        if key.startswith("DESTINATION_"):
            field = key[len("DESTINATION_"):]
            db_key = f"{db_type_upper}_{field}"
            lines.append(f"{db_key}={value}")

    for field in EXTRA_DB_FIELDS.get(db_type_upper, []):
        db_key = f"{db_type_upper}_{field}"
        if db_key in db_defaults:
            lines.append(f"{db_key}={db_defaults[db_key]}")

    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_path, backup_path


def restore_db_config(config_path, backup_path):
    if backup_path.exists():
        backup_content = backup_path.read_text(encoding="utf-8")
        if backup_content:
            config_path.write_text(backup_content, encoding="utf-8")
        else:
            config_path.unlink(missing_ok=True)
        backup_path.unlink(missing_ok=True)
    else:
        config_path.unlink(missing_ok=True)


def run_liquibase(dest_db_type):
    runner_map = {
        "MSSQL": "scripts/batch/mssql/setup/run_liquibase.bat",
        "MYSQL": "scripts/batch/mysql/setup/run_liquibase.bat",
        "POSTGRESQL": "scripts/batch/postgresql/setup/run_liquibase.bat",
    }

    runner_path = ROOT / runner_map.get(dest_db_type, "")
    if not runner_path.exists():
        print(f"ERROR: Liquibase runner not found: {runner_path}")
        return 1

    changelog = ROOT / "liquibase" / dest_db_type.lower() / "master.xml"
    if not changelog.exists():
        print(f"ERROR: Changelog not found: {changelog}")
        return 1

    changelog_rel = changelog.relative_to(ROOT)

    cmd = [
        "cmd", "/c",
        str(runner_path),
        str(changelog_rel),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode


def print_apply_summary(dest_db_type):
    print()
    print("=" * 48)
    print("APPLY SCHEMA")
    print("=" * 48)
    print()
    print(f"Destination Database : {dest_db_type}")
    print(f"Changelog            : liquibase/{dest_db_type.lower()}/master.xml")
    print()
    print("APPLY SCHEMA: PASS")
    print()
    return 0


def main():
    try:
        dest_effective, db_defaults = get_destination_config()
        dest_db_type = dest_effective.get("DESTINATION_DATABASE", "").upper()

        if not dest_db_type:
            print("ERROR: DESTINATION_DATABASE is not configured")
            return 1

        print()
        print("=" * 48)
        print("APPLY SCHEMA")
        print("=" * 48)
        print()
        print(f"Destination Database : {dest_db_type}")
        print()

        config_path = None
        backup_path = None
        try:
            config_path, backup_path = write_temp_db_config(dest_effective, db_defaults, dest_db_type)
            rc = run_liquibase(dest_db_type)
            if rc != 0:
                print("ERROR: Liquibase update failed")
                return rc
        finally:
            if config_path and backup_path:
                restore_db_config(config_path, backup_path)

        return print_apply_summary(dest_db_type)

    except Exception as e:
        print(f"ERROR: Schema apply failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
