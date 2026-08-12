import json
import re
from pathlib import Path

from scripts.python.common.liquibase_schema_helpers import (
    collect_existing_change_files,
    get_next_change_number,
)

ROOT = Path(__file__).resolve().parents[4]

schema_file = (
    ROOT
    / "metadata"
    / "postgresql"
    / "schema_registry.json"
)

datatype_file = (
    ROOT
    / "metadata"
    / "postgresql"
    / "datatype_registry.json"
)
liquibase_dir = (
    ROOT
    / "liquibase"
    / "postgresql"
)

liquibase_dir.mkdir(parents=True, exist_ok=True)

with open(schema_file, "r", encoding="utf-8") as f:
    schema_registry = json.load(f)
    
with open(datatype_file, "r", encoding="utf-8") as f:
    datatype_registry = json.load(f)

existing_files = sorted(
    f for f in liquibase_dir.glob("*.xml")
    if f.name != "master.xml"
)

existing_changes = collect_existing_change_files(
    liquibase_dir,
    exclude_names={"master.xml"},
)

covered_columns = {}
for parsed in existing_changes:
    covered_columns.setdefault(parsed["table_name"], set()).update(parsed["columns"])

next_number = get_next_change_number(existing_files)
print(f"Using next change number: {next_number:03d}")

generated_any = False


for table_name, columns in schema_registry.items():

    table_name = table_name.lower()

    clean_columns = [
        c.replace("\ufeff", "").strip()
        for c in columns
    ]

    already_covered = covered_columns.get(
        table_name,
        set()
    )

    new_columns = [
        c
        for c in clean_columns
        if c.lower() not in already_covered
    ]


    if not new_columns:

        # No schema changes detected for this table

        continue


    change_id = f"{next_number:03d}"


    # ============================================
    # CREATE NEW TABLE
    # ============================================

    if table_name not in covered_columns:

        filename = (
            f"{change_id}_create_{table_name}.xml"
        )

        xml_path = liquibase_dir / filename


        column_xml = ""

        for col in new_columns:
    
            datatype = (
                datatype_registry
                .get(table_name, {})
                .get(col, {})
                .get("selected_type", "TEXT")
            )

            column_xml += f'''
                <column name="{col}" type="{datatype}"/>

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
                <tableExists
                    schemaName="public"
                    tableName="{table_name}"/>
            </not>

        </preConditions>

        <createTable
            schemaName="public"
            tableName="{table_name}">

{column_xml}

        </createTable>

    </changeSet>

</databaseChangeLog>
'''


    # ============================================
    # ALTER EXISTING TABLE
    # ============================================

    else:

        filename = (
            f"{change_id}_alter_"
            f"{table_name}_add_columns.xml"
        )

        xml_path = liquibase_dir / filename


        add_column_xml = ""

        precondition_checks = ""


        for col in new_columns:
            
            datatype = (
                datatype_registry
                .get(table_name, {})
                .get(col, {})
                .get("selected_type", "TEXT")
            )

            add_column_xml += f'''
                <column name="{col}" type="{datatype}"/>
        '''

            precondition_checks += f'''
            <not>
                <columnExists
                    schemaName="public"
                    tableName="{table_name}"
                    columnName="{col}"/>
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

        <addColumn
            schemaName="public"
            tableName="{table_name}">

{add_column_xml}

        </addColumn>

    </changeSet>

</databaseChangeLog>
'''

    if xml_path.exists():
        raise RuntimeError(
            f"IMMUTABLE CHANGESET VIOLATION: "
            f"Unable to write new changeset {xml_path.name} because a file with the same name already exists. "
            f"Please inspect existing Liquibase files in {liquibase_dir}."
        )

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    print(f"Generated {filename}")

    covered_columns.setdefault(
        table_name,
        set()
    ).update(
        c.lower()
        for c in new_columns
    )

    next_number += 1

    generated_any = True


if not generated_any:

    print(
        "No schema changes detected. "
        "Nothing to generate."
    )