import json
import re
from pathlib import Path


# =========================================================
# PATHS
# =========================================================

ROOT = Path(__file__).resolve().parents[4]

schema_file = ROOT / "metadata" / "mysql" / "schema_registry.json"
datatype_registry_file = ROOT / "metadata" / "mysql" / "datatype_registry.json"
liquibase_dir = ROOT / "liquibase" / "mysql"1

liquibase_dir.mkdir(parents=True, exist_ok=True)


# =========================================================
# LOAD SCHEMA REGISTRY
# =========================================================

with open(schema_file, "r", encoding="utf-8") as f:
    schema_registry = json.load(f)


# =========================================================
# LOAD DATATYPE REGISTRY
# =========================================================

if datatype_registry_file.exists():
    with open(datatype_registry_file, "r", encoding="utf-8") as f:
        datatype_registry = json.load(f)
else:
    datatype_registry = {}


# =========================================================
# DATATYPE RESOLUTION
# =========================================================

def get_column_datatype(table_name, column_name):
    """
    Get final datatype from datatype_registry.json.

    Priority:
        1. final_type
        2. selected_type
        3. detected_type
        4. VARCHAR(255)
    """

    table_metadata = datatype_registry.get(table_name, {})

    if not isinstance(table_metadata, dict):
        return "VARCHAR(255)"

    column_metadata = table_metadata.get(column_name, {})

    if not isinstance(column_metadata, dict):
        return "VARCHAR(255)"

    # Highest priority: final_type
    final_type = column_metadata.get("final_type")

    if isinstance(final_type, str) and final_type.strip():
        return final_type.strip().upper()

    # Second priority: selected_type
    selected_type = column_metadata.get("selected_type")

    if isinstance(selected_type, str) and selected_type.strip():
        return selected_type.strip().upper()

    # Third priority: detected_type
    detected_type = column_metadata.get("detected_type")

    if isinstance(detected_type, str) and detected_type.strip():
        return detected_type.strip().upper()

    # Safe fallback
    return "VARCHAR(255)"


# =========================================================
# EXISTING LIQUIBASE FILES
# =========================================================

existing_files = sorted(
    f
    for f in liquibase_dir.glob("*.xml")
    if f.name != "master.xml"
)


# =========================================================
# FIND ALREADY COVERED TABLES/COLUMNS
# =========================================================

covered_columns = {}

column_pattern = re.compile(r'<column\s+name="([^"]+)"')
table_pattern = re.compile(r'tableName="([^"]+)"')


for file in existing_files:
    try:
        content = file.read_text(encoding="utf-8")

        table_match = table_pattern.search(content)

        if not table_match:
            continue

        table_name = table_match.group(1).lower()

        columns = {
            column.lower()
            for column in column_pattern.findall(content)
        }

        covered_columns.setdefault(
            table_name,
            set()
        ).update(columns)

    except Exception:
        pass


# =========================================================
# GENERATE CHANGESETS
# =========================================================

next_number = len(existing_files) + 1
generated_any = False


for table_name, columns in sorted(schema_registry.items()):

    table_name = table_name.lower()

    clean_columns = [
        column.replace("\ufeff", "").strip()
        for column in columns
    ]

    already_covered = covered_columns.get(
        table_name,
        set()
    )

    new_columns = [
        column
        for column in clean_columns
        if column.lower() not in already_covered
    ]

    # Nothing new for this table
    if not new_columns:
        continue

    change_id = f"{next_number:03d}"


    # =====================================================
    # NEW TABLE
    # =====================================================

    if table_name not in covered_columns:

        filename = f"{change_id}_create_{table_name}.xml"
        xml_path = liquibase_dir / filename

        column_xml = ""

        for column in new_columns:

            datatype = get_column_datatype(
                table_name,
                column
            )

            print(
                f"{table_name}.{column} -> {datatype}"
            )

            column_xml += (
                f'        <column '
                f'name="{column}" '
                f'type="{datatype}"/>\n'
            )


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
{column_xml}        </createTable>

    </changeSet>

</databaseChangeLog>
'''


    # =====================================================
    # EXISTING TABLE - ADD NEW COLUMNS
    # =====================================================

    else:

        filename = (
            f"{change_id}_alter_"
            f"{table_name}_add_columns.xml"
        )

        xml_path = liquibase_dir / filename

        add_column_xml = ""
        precondition_checks = ""


        for column in new_columns:

            datatype = get_column_datatype(
                table_name,
                column
            )

            print(
                f"{table_name}.{column} -> {datatype}"
            )

            add_column_xml += (
                f'        <column '
                f'name="{column}" '
                f'type="{datatype}"/>\n'
            )

            precondition_checks += f'''            <not>
                <columnExists
                    tableName="{table_name}"
                    columnName="{column}"
                />
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
{precondition_checks}            </and>
        </preConditions>

        <addColumn tableName="{table_name}">
{add_column_xml}        </addColumn>

    </changeSet>

</databaseChangeLog>
'''


    # =====================================================
    # WRITE GENERATED XML
    # =====================================================

    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_content)

    print(f"Generated {filename}")


    # Update in-memory coverage
    covered_columns.setdefault(
        table_name,
        set()
    ).update(
        column.lower()
        for column in new_columns
    )

    next_number += 1
    generated_any = True


# =========================================================
# SCHEMA STATUS
# =========================================================

if not generated_any:
    print("No schema changes detected. Nothing to generate.")


status_file = ROOT / "metadata" / "mysql" / "schema_status.json"

status_file.parent.mkdir(
    parents=True,
    exist_ok=True
)


with open(status_file, "w", encoding="utf-8") as f:
    json.dump(
        {
            "schema_changed": generated_any
        },
        f,
        indent=4
    )


print(f"Schema changed: {generated_any}")