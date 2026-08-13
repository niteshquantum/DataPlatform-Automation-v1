import os
import platform
import sys
import subprocess
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
)


def load_db_defaults():
    db_defaults = {}
    for db_name in ["mssql", "mysql", "postgresql"]:
        db_defaults.update(load_migration_config(db_name))
    return db_defaults


def get_destination_config():
    dest_defaults = load_migration_role_config("destination")
    db_defaults = load_db_defaults()
    dest_effective = build_effective_config(dest_defaults, db_defaults, "DESTINATION")
    return dest_effective


def run_migration_liquibase(dest_effective):
    if platform.system() == "Windows":
        runner_path = ROOT / "scripts" / "batch" / "migration" / "windows" / "run_liquibase.bat"
    else:
        runner_path = ROOT / "scripts" / "bash" / "migration" / "linux" / "run_liquibase.sh"

    if not runner_path.exists():
        print(f"ERROR: Migration Liquibase runner not found: {runner_path}")
        return 1

    dest_db_type = dest_effective.get("DESTINATION_DATABASE", "").upper()
    changelog = ROOT / "liquibase" / "migration" / dest_db_type.lower() / "master.xml"
    if not changelog.exists():
        print(f"ERROR: Migration changelog not found: {changelog}")
        return 1

    changelog_rel = changelog.relative_to(ROOT)

    if platform.system() == "Windows":
        cmd = [
            "cmd", "/c",
            str(runner_path),
            dest_db_type,
            str(changelog_rel),
            "update",
            dest_effective.get("DESTINATION_HOST", ""),
            dest_effective.get("DESTINATION_PORT", ""),
            dest_effective.get("DESTINATION_DB", ""),
            dest_effective.get("DESTINATION_USER", ""),
            dest_effective.get("DESTINATION_PASSWORD", ""),
        ]
    else:
        cmd = [
            str(runner_path),
            dest_db_type,
            str(changelog_rel),
            "update",
            dest_effective.get("DESTINATION_HOST", ""),
            dest_effective.get("DESTINATION_PORT", ""),
            dest_effective.get("DESTINATION_DB", ""),
            dest_effective.get("DESTINATION_USER", ""),
            dest_effective.get("DESTINATION_PASSWORD", ""),
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode


def print_apply_summary(dest_effective):
    dest_db_type = dest_effective.get("DESTINATION_DATABASE", "").upper()

    print()
    print("=" * 48)
    print("APPLY SCHEMA")
    print("=" * 48)
    print()
    print(f"Destination Database : {dest_db_type}")
    print(f"Host                 : {dest_effective.get('DESTINATION_HOST', '')}")
    print(f"Port                 : {dest_effective.get('DESTINATION_PORT', '')}")
    print(f"DB                   : {dest_effective.get('DESTINATION_DB', '')}")
    print(f"User                 : {dest_effective.get('DESTINATION_USER', '')}")
    print(f"Password             : {mask_password(dest_effective.get('DESTINATION_PASSWORD', ''))}")
    print(f"Changelog            : liquibase/migration/{dest_db_type.lower()}/master.xml")
    print()
    print("APPLY SCHEMA: PASS")
    print()
    return 0


def main():
    try:
        dest_effective = get_destination_config()
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

        rc = run_migration_liquibase(dest_effective)
        if rc != 0:
            print("ERROR: Liquibase update failed")
            return rc

        return print_apply_summary(dest_effective)

    except Exception as e:
        print(f"ERROR: Schema apply failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
