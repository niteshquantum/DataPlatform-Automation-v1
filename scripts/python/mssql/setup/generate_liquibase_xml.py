"""Generate immutable MSSQL Liquibase changelogs from current source metadata."""
import hashlib
import json
import os
import re
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[4]
SCHEMA_FILE = ROOT / "metadata" / "mssql" / "schema_registry.json"
DATATYPE_FILE = ROOT / "metadata" / "mssql" / "datatype_registry.json"
RENAME_FILE = ROOT / "metadata" / "mssql" / "schema_renames.json"
LIQUIBASE_DIR = ROOT / "liquibase" / "mssql"
STATUS_FILE = ROOT / "metadata" / "mssql" / "schema_status.json"
MANIFEST_FILE = ROOT / "metadata" / "mssql" / "migration_manifest.json"
NS = "http://www.liquibase.org/xml/ns/dbchangelog"
LIQUIBASE_DIR.mkdir(parents=True, exist_ok=True)


def normalize(value):
    return str(value).replace("\ufeff", "").strip().lower()


def type_token(value):
    return re.sub(r"[^a-z0-9]+", "", str(value).lower()) or "unknown"


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_json(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def source_changesets():
    """Return immutable (id, author) identities represented by source XML."""
    result = {}
    for path in sorted(LIQUIBASE_DIR.glob("*.xml")):
        if path.name in {"master.xml", "master_objects.xml"}:
            continue
        root = ET.parse(path).getroot()
        for changeset in root.findall(f"{{{NS}}}changeSet"):
            identity = (changeset.get("id"), changeset.get("author"))
            if not all(identity) or identity in result:
                raise RuntimeError(f"IMMUTABLE_CHANGESET_VIOLATION: duplicate or invalid source identity in {path.name}")
            result[identity] = {"file": path.name, "sha256": _sha256(path)}
    return result


def _read_conf(path):
    return dict(line.strip().split("=", 1) for line in path.read_text(encoding="utf-8").splitlines()
                if "=" in line and not line.lstrip().startswith("#"))


def applied_changesets():
    """Read target history only; this function never modifies it."""
    config_path = ROOT / "config" / "ubuntu" / "mssql.conf"
    if not config_path.exists():
        return []
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("MSSQL_MIGRATION_HISTORY_CHECK_UNAVAILABLE: pyodbc is required to verify DATABASECHANGELOG") from exc
    config = _read_conf(config_path)
    driver = config.get("MSSQL_DRIVER", config.get("MSSQL_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")).strip('"')
    try:
        connection = pyodbc.connect(
            f"DRIVER={{{driver}}};SERVER={config['MSSQL_HOST']},{config.get('MSSQL_PORT', '1433')};"
            f"DATABASE={os.environ.get('MSSQL_DATABASE', config['MSSQL_DB'])};UID={config['MSSQL_USER']};PWD={config.get('MSSQL_PASSWORD', '')};"
            "Encrypt=yes;TrustServerCertificate=yes;"
        )
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT ID, AUTHOR, FILENAME FROM DATABASECHANGELOG")
            return [(str(row[0]), str(row[1]), str(row[2])) for row in cursor.fetchall()]
        finally:
            connection.close()
    except Exception as exc:
        if "DATABASECHANGELOG" in str(exc).upper() and "INVALID OBJECT" in str(exc).upper():
            return []
        raise RuntimeError(f"MSSQL_MIGRATION_HISTORY_CHECK_UNAVAILABLE: {exc}") from exc


def verify_applied_history(source, applied):
    for change_id, author, filename in applied:
        if "liquibase/mssql" in filename.replace("\\", "/").lower() and (change_id, author) not in source:
            raise RuntimeError("IMMUTABLE_MIGRATION_HISTORY_MISSING: "
                               f"Applied changeset mssql:{change_id}:{author} has no matching immutable source definition.")


def verify_manifest(source):
    if not MANIFEST_FILE.exists():
        return
    for entry in _read_json(MANIFEST_FILE, {}).get("migrations", []):
        identity = (str(entry.get("id")), str(entry.get("author")))
        actual = source.get(identity)
        if not actual or actual != {"file": entry.get("file"), "sha256": entry.get("sha256")}:
            raise RuntimeError("IMMUTABLE_MIGRATION_HISTORY_MISSING: "
                               f"Repository manifest entry mssql:{identity[0]}:{identity[1]} has no matching immutable source definition.")


def write_manifest(source):
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"migrations": [dict(id=key[0], author=key[1], **value) for key, value in sorted(source.items())]}
    content = json.dumps(payload, indent=2) + "\n"
    if not MANIFEST_FILE.exists() or MANIFEST_FILE.read_text(encoding="utf-8") != content:
        MANIFEST_FILE.write_text(content, encoding="utf-8")


def write_changeset(filename, content):
    path = LIQUIBASE_DIR / filename
    encoded = content.encode("utf-8")
    if path.exists():
        if path.read_bytes() == encoded:
            print(f"Unchanged {filename}")
            return False
        raise RuntimeError(f"IMMUTABLE_CHANGESET_VIOLATION: {filename} already exists with different content.")
    path.write_bytes(encoded)
    print(f"Generated {filename}")
    return True


def ordered_migration_files():
    files = {path.name: path for path in LIQUIBASE_DIR.glob("*.xml")
             if path.name not in {"master.xml", "master_objects.xml"}}
    master = LIQUIBASE_DIR / "master.xml"
    ordered = []
    if master.exists():
        root = ET.parse(master).getroot()
        for include in root.findall(f"{{{NS}}}include"):
            name = include.get("file")
            if name in files:
                ordered.append(files.pop(name))
    ordered.extend(files[name] for name in sorted(files))
    return ordered


def effective_repository_schema(applied_identities=None):
    """Apply schema changes in master include order to build repository state.

    When ``applied_identities`` is provided, only those changesets form the
    pre-migration baseline used for drift validation.
    """
    schema = {}
    for path in ordered_migration_files():
        root = ET.parse(path).getroot()
        for changeset in root.findall(f"{{{NS}}}changeSet"):
            identity = (changeset.get("id"), changeset.get("author"))
            if applied_identities is not None and identity not in applied_identities:
                continue
            for change in list(changeset):
                tag = change.tag.rsplit("}", 1)[-1]
                table = normalize(change.get("tableName", ""))
                if tag == "createTable":
                    columns = schema.setdefault(table, {})
                    for column in change.findall(f"{{{NS}}}column"):
                        columns[normalize(column.get("name"))] = {"name": column.get("name"), "type": column.get("type", "VARCHAR(255)").upper()}
                elif tag == "addColumn":
                    columns = schema.setdefault(table, {})
                    for column in change.findall(f"{{{NS}}}column"):
                        columns[normalize(column.get("name"))] = {"name": column.get("name"), "type": column.get("type", "VARCHAR(255)").upper()}
                elif tag == "dropColumn" and table in schema:
                    schema[table].pop(normalize(change.get("columnName")), None)
                elif tag == "renameColumn" and table in schema:
                    old, new = normalize(change.get("oldColumnName")), change.get("newColumnName")
                    detail = schema[table].pop(old, None)
                    if detail:
                        detail["name"] = new
                        schema[table][normalize(new)] = detail
                elif tag == "modifyDataType" and table in schema:
                    detail = schema[table].get(normalize(change.get("columnName")))
                    if detail:
                        detail["type"] = change.get("newDataType", detail["type"]).upper()
    return schema


def get_column_datatype(table_name, column_name, registry):
    table = registry.get(table_name) or registry.get(normalize(table_name)) or {}
    if isinstance(table, dict):
        metadata = table.get(column_name) or table.get(normalize(column_name)) or {}
        if isinstance(metadata, dict):
            for key in ("final_type", "selected_type", "detected_type"):
                value = metadata.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip().upper()
    return "VARCHAR(255)"


def changelog(change_id, body):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">
    <changeSet id="{change_id}" author="tanisha">
{body}    </changeSet>
</databaseChangeLog>
'''


def declared_renames():
    """Explicit mappings are the only unambiguous evidence for a rename."""
    data = _read_json(RENAME_FILE, {})
    return {normalize(table): {normalize(old): new for old, new in mapping.items()}
            for table, mapping in data.items() if isinstance(mapping, dict)}


def main():
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    source = source_changesets()
    verify_manifest(source)
    verify_applied_history(source, applied_changesets())
    if not SCHEMA_FILE.exists():
        STATUS_FILE.write_text(json.dumps({"schema_changed": False, "reason": "no_schema_registry"}, indent=4), encoding="utf-8")
        write_manifest(source)
        return

    current = _read_json(SCHEMA_FILE, {})
    types = _read_json(DATATYPE_FILE, {})
    previous, generated = effective_repository_schema(), False
    renames = declared_renames()
    for raw_table, raw_columns in sorted(current.items()):
        table = normalize(raw_table)
        columns = [str(c).replace("\ufeff", "").strip() for c in raw_columns]
        current_by_key = {normalize(c): c for c in columns}
        prior = previous.get(table, {})
        if not prior:
            if not columns:
                continue
            change_id = f"mssql-create-{table}"
            body = "        <preConditions onFail=\"HALT\"><not><tableExists tableName=\"%s\"/></not></preConditions>\n        <createTable tableName=\"%s\">\n" % (table, table)
            body += "".join(f'            <column name="{column}" type="{get_column_datatype(raw_table, column, types)}"/>\n' for column in columns)
            body += "        </createTable>\n"
            generated = write_changeset(f"{change_id}.xml", changelog(change_id, body)) or generated
            continue

        prior_keys = set(prior)
        added, removed = set(current_by_key) - prior_keys, prior_keys - set(current_by_key)
        table_renames = renames.get(table, {})
        valid_renames = {old: new for old, new in table_renames.items()
                         if old in removed and normalize(new) in added}
        if valid_renames:
            for old, new in sorted(valid_renames.items()):
                new_key = normalize(new)
                change_id = f"mssql-rename-{table}-{old}-{new_key}"
                body = (f'        <preConditions onFail="HALT"><and><columnExists tableName="{table}" columnName="{prior[old]["name"]}"/>'
                        f'<not><columnExists tableName="{table}" columnName="{new}"/></not></and></preConditions>\n'
                        f'        <renameColumn tableName="{table}" oldColumnName="{prior[old]["name"]}" newColumnName="{new}"/>\n')
                generated = write_changeset(f"{change_id}.xml", changelog(change_id, body)) or generated
                removed.remove(old); added.remove(new_key)
                prior[new_key] = dict(prior.pop(old), name=new)

        if removed:
            names = [prior[key]["name"] for key in sorted(removed)]
            change_id = f"mssql-drop-{table}-{'-'.join(normalize(name) for name in names)}"
            body = "        <preConditions onFail=\"HALT\"><and>\n" + "".join(f'            <columnExists tableName="{table}" columnName="{name}"/>\n' for name in names) + "        </and></preConditions>\n"
            body += "".join(f'        <dropColumn tableName="{table}" columnName="{name}"/>\n' for name in names)
            generated = write_changeset(f"{change_id}.xml", changelog(change_id, body)) or generated

        if added:
            names = [current_by_key[key] for key in sorted(added)]
            change_id = f"mssql-add-{table}-{'-'.join(normalize(name) for name in names)}"
            body = "        <preConditions onFail=\"HALT\"><and>\n" + "".join(f'            <not><columnExists tableName="{table}" columnName="{name}"/></not>\n' for name in names) + "        </and></preConditions>\n"
            body += f'        <addColumn tableName="{table}">\n' + "".join(f'            <column name="{name}" type="{get_column_datatype(raw_table, name, types)}"/>\n' for name in names) + "        </addColumn>\n"
            generated = write_changeset(f"{change_id}.xml", changelog(change_id, body)) or generated

        for key in sorted(set(current_by_key) & set(prior)):
            old_type = prior[key]["type"].upper()
            new_type = get_column_datatype(raw_table, current_by_key[key], types)
            if old_type == new_type:
                continue
            change_id = f"mssql-modify-{table}-{key}-{type_token(old_type)}-to-{type_token(new_type)}"
            body = (f'        <preConditions onFail="HALT"><columnExists tableName="{table}" columnName="{prior[key]["name"]}"/></preConditions>\n'
                    f'        <modifyDataType tableName="{table}" columnName="{prior[key]["name"]}" newDataType="{new_type}"/>\n')
            generated = write_changeset(f"{change_id}.xml", changelog(change_id, body)) or generated

    write_manifest(source_changesets())
    STATUS_FILE.write_text(json.dumps({"schema_changed": generated}, indent=4), encoding="utf-8")
    print(f"Schema changed: {generated}")


if __name__ == "__main__":
    main()
