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


def load_db_defaults():
    db_defaults = {}
    for db_file in ["mssql.conf", "mysql.conf", "postgresql.conf"]:
        db_defaults.update(load_migration_config(db_file))
    return db_defaults


def get_destination_db_type():
    dest_defaults = load_migration_config("destination.conf")
    db_defaults = load_db_defaults()
    dest_effective = build_effective_config(dest_defaults, db_defaults, "DESTINATION")
    return dest_effective.get("DESTINATION_DATABASE", "").upper()


def run_generator(dest_db_type):
    generator_map = {
        "MSSQL": "scripts/python/mssql/setup/generate_liquibase_xml.py",
        "MYSQL": "scripts/python/mysql/setup/generate_liquibase_xml.py",
        "POSTGRESQL": "scripts/python/postgresql/setup/generate_liquibase_xml.py",
    }

    generator_path = ROOT / generator_map.get(dest_db_type, "")
    if not generator_path.exists():
        print(f"ERROR: Generator not found: {generator_path}")
        return 1

    print(f"Running generator: {generator_path.name}")
    result = subprocess.run(
        [sys.executable, str(generator_path)],
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode


def ensure_master_objects_xml(liquibase_dir):
    master_objects = liquibase_dir / "master_objects.xml"
    if not master_objects.exists():
        master_objects.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"\n'
            '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
            '        xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog\n'
            '        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">\n'
            '</databaseChangeLog>\n',
            encoding="utf-8",
        )
        print(f"Created empty {master_objects.name}")
    return master_objects


def update_master_xml(liquibase_dir):
    xml_files = sorted([
        f.name for f in liquibase_dir.glob("*.xml")
        if f.name != "master.xml"
    ])

    includes = "\n".join([
        f'<include file="{fname}" relativeToChangelogFile="true" />'
        for fname in xml_files
    ])

    master_path = liquibase_dir / "master.xml"
    content = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"\n'
        '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
        '        xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog\n'
        '        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">\n'
        f"{includes}\n"
        '</databaseChangeLog>\n'
    )

    master_path.write_text(content, encoding="utf-8")
    print(f"Updated {master_path.name} with {len(xml_files)} include(s)")
    return master_path


def print_generation_summary(dest_db_type):
    liquibase_dir = ROOT / "liquibase" / dest_db_type.lower()

    print()
    print("=" * 48)
    print("GENERATE TARGET DDL")
    print("=" * 48)
    print()
    print(f"Destination Database : {dest_db_type}")
    print(f"Liquibase Directory   : {liquibase_dir}")
    print()

    xml_files = sorted([
        f for f in liquibase_dir.glob("*.xml")
        if f.name not in ("master.xml", "master_objects.xml")
    ])

    print(f"Generated Files      : {len(xml_files)}")
    for f in xml_files:
        print(f"  - {f.name}")
    print()

    print("GENERATE TARGET DDL: PASS")
    print()
    return 0


def main():
    try:
        dest_db_type = get_destination_db_type()

        if not dest_db_type:
            print("ERROR: DESTINATION_DATABASE is not configured")
            return 1

        print()
        print("=" * 48)
        print("GENERATE TARGET DDL")
        print("=" * 48)
        print()
        print(f"Destination Database : {dest_db_type}")
        print()

        liquibase_dir = ROOT / "liquibase" / dest_db_type.lower()
        liquibase_dir.mkdir(parents=True, exist_ok=True)

        rc = run_generator(dest_db_type)
        if rc != 0:
            print("ERROR: DDL generation failed")
            return rc

        ensure_master_objects_xml(liquibase_dir)
        update_master_xml(liquibase_dir)

        return print_generation_summary(dest_db_type)

    except Exception as e:
        print(f"ERROR: DDL generation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
