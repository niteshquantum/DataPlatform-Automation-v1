import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]

schema_file = ROOT / "metadata" / "mysql" / "schema_registry.json"
datatype_registry_file = ROOT / "metadata" / "mysql" / "datatype_registry.json"
liquibase_dir = ROOT / "liquibase" / "mysql"
liquibase_dir.mkdir(parents=True, exist_ok=True)

if not schema_file.exists():
    raise FileNotFoundError(f"Schema registry missing: {schema_file}")

with open(schema_file, "r", encoding="utf-8") as f:
    schema_registry = json.load(f)

if datatype_registry_file.exists():
    with open(datatype_registry_file, "r", encoding="utf-8") as f:
        datatype_registry = json.load(f)
else:
    datatype_registry = {}


def _normalize_name(value):
    return str(value).strip().replace("\ufeff", "").lower()


def get_column_datatype(table_name, column_name):
    """Resolve datatype with final_type > selected_type > detected_type > safe fallback."""
    table_metadata = datatype_registry.get(table_name, {})
    if not isinstance(table_metadata, dict):
        return "VARCHAR(255)"
    column_metadata = table_metadata.get(column_name, {})
    if not isinstance(column_metadata, dict):
        return "VARCHAR(255)"
    for key in ("final_type", "selected_type", "detected_type"):
        value = column_metadata.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().upper()
    return "VARCHAR(255)"


def parse_existing_table_types():
    existing_types = {}
    files = sorted(f for f in liquibase_dir.glob("*.xml") if f.name != "master.xml")
    table_pattern = re.compile(r'tableName="([^"]+)"')
    column_pattern = re.compile(r'<column\s+name="([^"]+)"\s+type="([^"]+)"')
    for file in files:
        try:
            content = file.read_text(encoding="utf-8")
            table_match = table_pattern.search(content)
            if not table_match:
                continue
            table_name = table_match.group(1).lower()
            existing_types.setdefault(table_name, {})
            for col_name, col_type in column_pattern.findall(content):
                existing_types[table_name][col_name.lower()] = col_type.upper()
        except Exception:
            continue
    return existing_types


existing_files = sorted(f for f in liquibase_dir.glob("*.xml") if f.name != "master.xml")
previous_types = parse_existing_table_types()
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
        columns = {column.lower() for column in column_pattern.findall(content)}
        covered_columns.setdefault(table_name, set()).update(columns)
    except Exception:
        pass


def detect_safe_rename(existing_columns, current_columns):
    existing_set = {_normalize_name(c) for c in existing_columns}
    current_set = {_normalize_name(c) for c in current_columns}
    deleted = [c for c in existing_columns if _normalize_name(c) not in current_set]
    added = [c for c in current_columns if _normalize_name(c) not in existing_set]
    if len(deleted) != 1 or len(added) != 1:
        return {}
    old_name = deleted[0]
    new_name = added[0]
    old_norm = _normalize_name(old_name)
    new_norm = _normalize_name(new_name)
    if old_norm == new_norm:
        return {old_name: new_name}
    old_tokens = [token for token in old_norm.split("_") if token]
    new_tokens = [token for token in new_norm.split("_") if token]
    prefix = 0
    while prefix < min(len(old_tokens), len(new_tokens)) and old_tokens[prefix] == new_tokens[prefix]:
        prefix += 1
    suffix = 0
    while suffix < min(len(old_tokens) - prefix, len(new_tokens) - prefix) and old_tokens[-1 - suffix] == new_tokens[-1 - suffix]:
        suffix += 1
    old_core = old_tokens[prefix:len(old_tokens) - suffix] if suffix else old_tokens[prefix:]
    new_core = new_tokens[prefix:len(new_tokens) - suffix] if suffix else new_tokens[prefix:]
    if not old_core or not new_core:
        return {old_name: new_name}
    if old_core == new_core:
        return {old_name: new_name}
    if len(old_core) == 1 and len(new_core) == 1 and old_core[0] != new_core[0]:
        return {old_name: new_name}
    return {}
def is_indexed_column(table_name, column_name):
    """
    Check whether a column is part of a generated MySQL index.
    """

    indexes_dir = (
        ROOT
        / "objects"
        / "mysql"
        / "generated"
        / "indexes"
    )

    if not indexes_dir.exists():
        return False

    table_name = _normalize_name(table_name)
    column_name = _normalize_name(column_name)

    for sql_file in indexes_dir.glob("*.sql"):
        try:
            sql = sql_file.read_text(
                encoding="utf-8"
            )

            # CREATE INDEX index_name ON table_name (column_name)
            match = re.search(
                r"CREATE\s+INDEX\s+[`\"]?([^`\"\s]+)[`\"]?"
                r"\s+ON\s+[`\"]?([^`\"\s]+)[`\"]?"
                r"\s*\(\s*[`\"]?([^`\"\s]+)[`\"]?\s*\)",
                sql,
                re.IGNORECASE
            )

            if not match:
                continue

            indexed_table = _normalize_name(match.group(2))
            indexed_column = _normalize_name(match.group(3))

            if (
                indexed_table == table_name
                and indexed_column == column_name
            ):
                return True

        except Exception:
            continue

    return False

def write_change_set(filename, xml_content):
    path = liquibase_dir / filename
    if path.exists():
        existing_content = path.read_text(encoding="utf-8")
        if existing_content == xml_content:
            print(f"Unchanged {filename}")
            return False
        raise RuntimeError(
            f"IMMUTABLE CHANGESET VIOLATION: Existing file {path.name} differs "
            "from regenerated content. Do not overwrite applied changelogs."
        )
    path.write_text(xml_content, encoding="utf-8")
    print(f"Generated {filename}")
    return True


generated_any = False

for table_name, columns in sorted(schema_registry.items()):
    table_name = str(table_name).lower()
    clean_columns = [str(column).replace("\ufeff", "").strip() for column in columns]
    previous_columns = list(covered_columns.get(table_name, set()))
    safe_rename = detect_safe_rename(previous_columns, clean_columns) if previous_columns else {}
    if not previous_columns:
        new_columns = clean_columns
        if not new_columns:
            continue
        change_id = f"mysql-create-{table_name}"
        filename = f"{change_id}.xml"
        column_xml = "".join(f'        <column name="{column}" type="{get_column_datatype(table_name, column)}"/>\n' for column in clean_columns)
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">
    <changeSet id="{change_id}" author="tanisha">
        <preConditions onFail="MARK_RAN">
            <not><tableExists tableName="{table_name}"/></not>
        </preConditions>
        <createTable tableName="{table_name}">
{column_xml}        </createTable>
    </changeSet>
</databaseChangeLog>
'''
        write_change_set(filename, xml_content)
        generated_any = True
        continue

    existing_named = {str(c).lower(): c for c in previous_columns}
    current_named = {str(c).lower(): c for c in clean_columns}
    new_columns = [column for column in clean_columns if _normalize_name(column) not in { _normalize_name(c) for c in previous_columns }]
    removed_columns = [column for column in previous_columns if _normalize_name(column) not in { _normalize_name(c) for c in clean_columns }]

    if safe_rename:
        old_name, new_name = next(iter(safe_rename.items()))
        change_id = f"mysql-rename-{table_name}-{_normalize_name(old_name)}-{_normalize_name(new_name)}"
        filename = f"{change_id}.xml"
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">
    <changeSet id="{change_id}" author="tanisha">
        <preConditions onFail="MARK_RAN">
            <columnExists tableName="{table_name}" columnName="{old_name}"/>
            <not><columnExists tableName="{table_name}" columnName="{new_name}"/></not>
        </preConditions>
        <renameColumn tableName="{table_name}" oldColumnName="{old_name}" newColumnName="{new_name}"/>
    </changeSet>
</databaseChangeLog>
'''
        write_change_set(filename, xml_content)
        generated_any = True
        continue

    if removed_columns:
        change_id = f"mysql-drop-{table_name}-{'-'.join(_normalize_name(c) for c in removed_columns)}"
        filename = f"{change_id}.xml"
        drop_column_xml = "".join(f'        <dropColumn tableName="{table_name}" columnName="{column}"/>\n' for column in removed_columns)
        conditions = "".join(f'            <columnExists tableName="{table_name}" columnName="{column}"/>\n' for column in removed_columns)
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">
    <changeSet id="{change_id}" author="tanisha">
        <preConditions onFail="MARK_RAN"><and>
{conditions}        </and></preConditions>
{drop_column_xml}    </changeSet>
</databaseChangeLog>
'''
        write_change_set(filename, xml_content)
        generated_any = True

    if new_columns:
        change_id = f"mysql-add-{table_name}-{'-'.join(_normalize_name(c) for c in new_columns)}"
        filename = f"{change_id}.xml"
        add_column_xml = "".join(f'        <column name="{column}" type="{get_column_datatype(table_name, column)}"/>\n' for column in new_columns)
        conditions = "".join(f'            <not><columnExists tableName="{table_name}" columnName="{column}"/></not>\n' for column in new_columns)
        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">
    <changeSet id="{change_id}" author="tanisha">
        <preConditions onFail="MARK_RAN"><and>
{conditions}        </and></preConditions>
        <addColumn tableName="{table_name}">
{add_column_xml}        </addColumn>
    </changeSet>
</databaseChangeLog>
'''
        write_change_set(filename, xml_content)
        generated_any = True

    for column in clean_columns:

        normalized = _normalize_name(column)

        old_type = previous_types.get(
            table_name,
            {}
        ).get(normalized)

        new_type = get_column_datatype(
            table_name,
            column
        )

        column_exists = (
            normalized
            in {
                _normalize_name(c)
                for c in previous_columns
            }
        )

        if not column_exists:
            continue

        if not old_type:
            continue

        if old_type == new_type:
            continue

        indexed = is_indexed_column(
            table_name,
            column
        )

        unsafe_indexed_type = (
            indexed
            and (
                new_type.startswith("TEXT")
                or new_type.startswith("BLOB")
            )
        )

        if unsafe_indexed_type:

            print(
                f"WARNING: Skipping unsafe datatype change "
                f"{table_name}.{column}: "
                f"{old_type} -> {new_type}. "
                f"The column is indexed and MySQL does not "
                f"allow a full TEXT/BLOB index without a key length."
            )

            continue

        change_id = (
            f"mysql-modify-"
            f"{table_name}-"
            f"{normalized}"
        )

        filename = f"{change_id}.xml"

        xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
    <databaseChangeLog
        xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="
            http://www.liquibase.org/xml/ns/dbchangelog
            http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

        <changeSet
            id="{change_id}"
            author="tanisha">

            <preConditions onFail="MARK_RAN">
                <columnExists
                    tableName="{table_name}"
                    columnName="{column}"/>
            </preConditions>

            <modifyDataType
                tableName="{table_name}"
                columnName="{column}"
                newDataType="{new_type}"/>

        </changeSet>

    </databaseChangeLog>
    '''

        write_change_set(
            filename,
            xml_content
        )

        generated_any = True

if not generated_any:
    print("No schema changes detected. Nothing to generate.")

status_file = ROOT / "metadata" / "mysql" / "schema_status.json"
status_file.parent.mkdir(parents=True, exist_ok=True)
with open(status_file, "w", encoding="utf-8") as f:
    json.dump({"schema_changed": generated_any}, f, indent=4)
print(f"Schema changed: {generated_any}")