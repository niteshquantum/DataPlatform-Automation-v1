import json
import re
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
)


def load_db_defaults():
    db_defaults = {}
    for db_name in ["mssql", "mysql", "postgresql"]:
        db_defaults.update(load_migration_config(db_name))
    return db_defaults


def get_destination_db_type():
    dest_defaults = load_migration_role_config("destination")
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


def update_migration_master_xml(liquibase_migration_dir):
    xml_files = sorted([
        f.name for f in liquibase_migration_dir.glob("*.xml")
        if f.name != "master.xml"
    ])

    includes = "\n".join([
        f'<include file="{fname}" relativeToChangelogFile="true" />'
        for fname in xml_files
    ])

    master_path = liquibase_migration_dir / "master.xml"
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
    print(f"Updated migration master.xml with {len(xml_files)} include(s)")
    return master_path


def generate_migration_ddl(dest_db_type):
    schema_file = ROOT / "metadata" / dest_db_type.lower() / "schema_registry.json"
    datatype_file = ROOT / "metadata" / dest_db_type.lower() / "datatype_registry.json"
    liquibase_migration_dir = ROOT / "liquibase" / "migration" / dest_db_type.lower()
    status_file = ROOT / "metadata" / dest_db_type.lower() / "schema_status.json"

    if not schema_file.exists():
        print(f"ERROR: Schema registry not found: {schema_file}")
        return 1

    with open(schema_file, "r", encoding="utf-8") as f:
        schema_registry = json.load(f)

    datatype_registry = {}
    if datatype_file.exists():
        with open(datatype_file, "r", encoding="utf-8") as f:
            datatype_registry = json.load(f)

    existing_files = sorted([
        f for f in liquibase_migration_dir.glob("*.xml")
        if f.name != "master.xml"
    ])

    covered_columns = {}

    column_pattern = re.compile(r'<column name="([^"]+)"')
    table_pattern = re.compile(r'tableName="([^"]+)"')

    for file in existing_files:
        try:
            content = file.read_text(encoding="utf-8")
            table_match = table_pattern.search(content)
            if not table_match:
                continue
            table_name = table_match.group(1).lower()
            cols = {c.lower() for c in column_pattern.findall(content)}
            covered_columns.setdefault(table_name, set()).update(cols)
        except Exception:
            pass

    next_number = len(existing_files) + 1
    generated_any = False


    def _get_column_type(table_name, column_name, registry):
        if not registry:
            return "VARCHAR(255)"
        try:
            from scripts.python.common.datatype_resolver import resolve_column_type
            return resolve_column_type(table_name, column_name, dest_db_type.lower(), registry)
        except Exception:
            return "VARCHAR(255)"


    for original_table_name, columns in sorted(schema_registry.items()):

        table_name = original_table_name.lower()
        clean_columns = [c.replace("\ufeff", "").strip() for c in columns]

        already_covered = covered_columns.get(table_name, set())
        new_columns = [c for c in clean_columns if c.lower() not in already_covered]

        if not new_columns:
            continue

        change_id = f"{next_number:03d}"

        if table_name not in covered_columns:
            filename = f"{change_id}_create_{table_name}.xml"
            xml_path = liquibase_migration_dir / filename

            column_xml = ""
            for col in new_columns:
                column_xml += f'''
        <column name="{col}" type="{_get_column_type(original_table_name, col, datatype_registry)}"/>
'''

            xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>

<databaseChangeLog
        xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="
        http://www.liquibase.org/xml/ns/dbchangelog
        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

    <changeSet id="{change_id}" author="tanisha">

    <preConditions onFail="MARK_RAN">
        <not>
            <tableExists tableName="{table_name}"/>
        </not>
    </preConditions>

    <createTable tableName="{table_name}">
{column_xml}
        </createTable>

    </changeSet>

</databaseChangeLog>
'''
        else:
            filename = f"{change_id}_alter_{table_name}_add_columns.xml"
            xml_path = liquibase_migration_dir / filename

            add_column_xml = ""
            precondition_checks = ""
            for col in new_columns:
                add_column_xml += f'''
        <column name="{col}" type="{_get_column_type(original_table_name, col, datatype_registry)}"/>
'''
                precondition_checks += f'''
            <not>
                <columnExists tableName="{table_name}" columnName="{col}"/>
            </not>
'''

            xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>

<databaseChangeLog
        xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="
        http://www.liquibase.org/xml/ns/dbchangelog
        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

    <changeSet id="{change_id}" author="tanisha">

    <preConditions onFail="MARK_RAN">
        <and>
{precondition_checks}
        </and>
    </preConditions>

    <addColumn tableName="{table_name}">
{add_column_xml}
        </addColumn>

    </changeSet>

</databaseChangeLog>
'''

        with open(xml_path, "w", encoding="utf-8") as f:
            f.write(xml_content)

        print(f"Generated {filename}")

        covered_columns.setdefault(table_name, set()).update(c.lower() for c in new_columns)
        next_number += 1
        generated_any = True

    if not generated_any:
        print("No schema changes detected. Nothing to generate.")

    status_file.parent.mkdir(parents=True, exist_ok=True)
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump({"schema_changed": generated_any}, f, indent=4)

    return 0


def print_generation_summary(dest_db_type):
    liquibase_migration_dir = ROOT / "liquibase" / "migration" / dest_db_type.lower()

    print()
    print("=" * 48)
    print("GENERATE TARGET DDL")
    print("=" * 48)
    print()
    print(f"Destination Database : {dest_db_type}")
    print(f"Liquibase Directory   : {liquibase_migration_dir}")
    print()

    xml_files = sorted([
        f for f in liquibase_migration_dir.glob("*.xml")
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

        liquibase_migration_dir = ROOT / "liquibase" / "migration" / dest_db_type.lower()
        liquibase_migration_dir.mkdir(parents=True, exist_ok=True)

        rc = generate_migration_ddl(dest_db_type)
        if rc != 0:
            print("ERROR: DDL generation failed")
            return rc

        ensure_master_objects_xml(liquibase_migration_dir)
        update_migration_master_xml(liquibase_migration_dir)

        return print_generation_summary(dest_db_type)

    except Exception as e:
        print(f"ERROR: DDL generation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
