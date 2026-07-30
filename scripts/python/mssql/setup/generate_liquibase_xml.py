import json
import re
from pathlib import Path
 
ROOT = Path(__file__).resolve().parents[4]
 
schema_file = ROOT / "metadata" / "mssql" / "schema_registry.json"
liquibase_dir = ROOT / "liquibase" / "mssql"
 
liquibase_dir.mkdir(parents=True, exist_ok=True)

if not schema_file.exists():

    print("No schema registry found. Nothing to generate.")
    print(f"Expected: {schema_file}")
    print("Run schema_detector.py first or create schema_registry.json manually.")
    schema_changed = False

    from pathlib import Path

    status_file = ROOT / "metadata" / "mssql" / "schema_status.json"

    status_file.parent.mkdir(parents=True, exist_ok=True)

    with open(status_file, "w", encoding="utf-8") as f:
        import json

        json.dump(
            {
                "schema_changed": False,
                "reason": "no_schema_registry",
            },
            f,
            indent=4,
        )

    exit(0)

with open(schema_file, "r", encoding="utf-8") as f:
    schema_registry = json.load(f)
 
existing_files = sorted(
    f for f in liquibase_dir.glob("*.xml")
    if f.name != "master.xml"
)

for old_file in existing_files:
    if old_file.name[0].isdigit():
        old_file.unlink()

existing_files = []
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
 
for table_name, columns in schema_registry.items():
    
    table_name = table_name.lower()
 
    clean_columns = [c.replace("\ufeff", "").strip() for c in columns]
 
    already_covered = covered_columns.get(table_name, set())
    new_columns = [c for c in clean_columns if c.lower() not in already_covered]
    print("=" * 80)
    print("TABLE              :", table_name)
    print("COVERED TABLES     :", list(covered_columns.keys()))
    print("ALREADY COVERED    :", sorted(already_covered))
    print("SCHEMA COLUMNS     :", clean_columns)
    print("NEW COLUMNS        :", new_columns)
    print("=" * 80)
    if not new_columns:
        # Nothing new for this table -> don't regenerate anything.
        continue
 
    change_id = f"{next_number:03d}"
 
    if table_name not in covered_columns:
        # Brand new table -> createTable changeset with all its columns.
        filename = f"{change_id}_create_{table_name}.xml"
        xml_path = liquibase_dir / filename
 
        column_xml = ""
        for col in new_columns:
            column_xml += f'''
        <column name="{col}" type="VARCHAR(255)"/>
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
        # Table already has a changeset -> only add the NEW columns.
        filename = f"{change_id}_alter_{table_name}_add_columns.xml"
        xml_path = liquibase_dir / filename
 
        add_column_xml = ""
        precondition_checks = ""
        for col in new_columns:
            add_column_xml += f'''
        <column name="{col}" type="VARCHAR(255)"/>
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

from pathlib import Path

status_file = ROOT / "metadata" / "mssql" / "schema_status.json"

status_file.parent.mkdir(parents=True, exist_ok=True)

with open(status_file, "w", encoding="utf-8") as f:
    json.dump(
        {
            "schema_changed": generated_any
        },
        f,
        indent=4
    )