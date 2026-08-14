"""Generate immutable MSSQL Liquibase changelogs from the schema registry."""
import hashlib
import json
import re
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[4]
SCHEMA_FILE = ROOT / "metadata" / "mssql" / "schema_registry.json"
LIQUIBASE_DIR = ROOT / "liquibase" / "mssql"
STATUS_FILE = ROOT / "metadata" / "mssql" / "schema_status.json"
MANIFEST_FILE = ROOT / "metadata" / "mssql" / "migration_manifest.json"
NS = "http://www.liquibase.org/xml/ns/dbchangelog"
LIQUIBASE_DIR.mkdir(parents=True, exist_ok=True)


def normalize(value):
    return str(value).replace("\ufeff", "").strip().lower()


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    return dict(
        line.strip().split("=", 1) for line in path.read_text(encoding="utf-8").splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    )


def applied_changesets():
    """Read the target history before generation; never use it to alter checksums."""
    config_path = ROOT / "config" / "ubuntu" / "mssql.conf"
    if not config_path.exists():
        return []  # isolated generator tests / fresh repository without a DB config
    try:
        import pyodbc
    except ImportError as exc:
        raise RuntimeError("MSSQL_MIGRATION_HISTORY_CHECK_UNAVAILABLE: pyodbc is required to verify DATABASECHANGELOG") from exc
    config = _read_conf(config_path)
    driver = config.get("MSSQL_DRIVER", config.get("MSSQL_ODBC_DRIVER", "ODBC Driver 18 for SQL Server")).strip('"')
    try:
        connection = pyodbc.connect(
            f"DRIVER={{{driver}}};SERVER={config['MSSQL_HOST']},{config.get('MSSQL_PORT', '1433')};"
            f"DATABASE={config['MSSQL_DB']};UID={config['MSSQL_USER']};PWD={config.get('MSSQL_PASSWORD', '')};"
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
            return []  # brand-new database; Liquibase has not created its history table yet
        raise RuntimeError(f"MSSQL_MIGRATION_HISTORY_CHECK_UNAVAILABLE: {exc}") from exc


def verify_applied_history(source, applied):
    """Fail before generation if DB history has no immutable repository artifact."""
    for change_id, author, filename in applied:
        is_mssql_source = "liquibase/mssql" in filename.replace("\\", "/").lower()
        if is_mssql_source and (change_id, author) not in source:
            raise RuntimeError(
                "IMMUTABLE_MIGRATION_HISTORY_MISSING: "
                f"Applied changeset mssql:{change_id}:{author} has no matching immutable source definition. "
                "A new migration must be created; the historical changeset must not be regenerated."
            )


def verify_manifest(source):
    """The committed manifest makes a fresh checkout detect lost XML artifacts."""
    if not MANIFEST_FILE.exists():
        return
    for entry in json.loads(MANIFEST_FILE.read_text(encoding="utf-8")).get("migrations", []):
        identity = (str(entry.get("id")), str(entry.get("author")))
        actual = source.get(identity)
        if not actual or actual != {"file": entry.get("file"), "sha256": entry.get("sha256")}:
            raise RuntimeError(
                "IMMUTABLE_MIGRATION_HISTORY_MISSING: "
                f"Repository manifest entry mssql:{identity[0]}:{identity[1]} has no matching immutable source definition."
            )


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


def discovered_columns():
    covered = {}
    for path in LIQUIBASE_DIR.glob("*.xml"):
        if path.name in {"master.xml", "master_objects.xml"}:
            continue
        content = path.read_text(encoding="utf-8")
        table = re.search(r'tableName="([^"]+)"', content)
        if table:
            covered.setdefault(normalize(table.group(1)), set()).update(normalize(c) for c in re.findall(r'<column\s+name="([^"]+)"', content))
    return covered


def changelog(change_id, body):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">
    <changeSet id="{change_id}" author="tanisha">
{body}    </changeSet>
</databaseChangeLog>
'''


def main():
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    source = source_changesets()
    verify_manifest(source)
    verify_applied_history(source, applied_changesets())
    if not SCHEMA_FILE.exists():
        STATUS_FILE.write_text(json.dumps({"schema_changed": False, "reason": "no_schema_registry"}, indent=4), encoding="utf-8")
        write_manifest(source)
        return
    schema, covered, generated = json.loads(SCHEMA_FILE.read_text(encoding="utf-8")), discovered_columns(), False
    for raw_table, raw_columns in sorted(schema.items()):
        table, columns = normalize(raw_table), [str(c).replace("\ufeff", "").strip() for c in raw_columns]
        new_columns = [c for c in columns if normalize(c) not in covered.get(table, set())]
        if not new_columns:
            continue
        if table not in covered:
            change_id = f"mssql-create-{table}"
            body = f'        <preConditions onFail="MARK_RAN"><not><tableExists tableName="{table}"/></not></preConditions>\n        <createTable tableName="{table}">\n' + "".join(f'            <column name="{c}" type="VARCHAR(255)"/>\n' for c in columns) + "        </createTable>\n"
        else:
            change_id = f"mssql-add-{table}-{'-'.join(normalize(c) for c in new_columns)}"
            body = "        <preConditions onFail=\"MARK_RAN\"><and>\n" + "".join(f'            <not><columnExists tableName="{table}" columnName="{c}"/></not>\n' for c in new_columns) + "        </and></preConditions>\n" + f'        <addColumn tableName="{table}">\n' + "".join(f'            <column name="{c}" type="VARCHAR(255)"/>\n' for c in new_columns) + "        </addColumn>\n"
        generated = write_changeset(f"{change_id}.xml", changelog(change_id, body)) or generated
        covered.setdefault(table, set()).update(normalize(c) for c in new_columns)
    write_manifest(source_changesets())
    STATUS_FILE.write_text(json.dumps({"schema_changed": generated}, indent=4), encoding="utf-8")
    print(f"Schema changed: {generated}")


if __name__ == "__main__":
    main()
