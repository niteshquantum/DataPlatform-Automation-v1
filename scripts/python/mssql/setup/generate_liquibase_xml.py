"""Generate immutable MSSQL Liquibase changelogs from the schema registry."""
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[4]
SCHEMA_FILE = ROOT / "metadata" / "mssql" / "schema_registry.json"
LIQUIBASE_DIR = ROOT / "liquibase" / "mssql"
STATUS_FILE = ROOT / "metadata" / "mssql" / "schema_status.json"
LIQUIBASE_DIR.mkdir(parents=True, exist_ok=True)


def normalize(value):
    return str(value).replace("\ufeff", "").strip().lower()


def write_changeset(filename, content):
    """Create once; byte-identical reruns are no-ops; all other reuse fails."""
    path = LIQUIBASE_DIR / filename
    encoded = content.encode("utf-8")
    if path.exists():
        if path.read_bytes() == encoded:
            print(f"Unchanged {filename}")
            return False
        raise RuntimeError(
            "IMMUTABLE_CHANGESET_VIOLATION: "
            f"{filename} already exists with different content. "
            "Create a new Liquibase changeset instead of modifying it."
        )
    path.write_bytes(encoded)
    print(f"Generated {filename}")
    return True


def discovered_columns():
    """Return the schema represented by historical create/add XML files."""
    covered = {}
    table_pattern = re.compile(r'tableName="([^"]+)"')
    column_pattern = re.compile(r'<column\s+name="([^"]+)"')
    for path in sorted(LIQUIBASE_DIR.glob("*.xml")):
        if path.name in {"master.xml", "master_objects.xml"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        table = table_pattern.search(content)
        if table:
            covered.setdefault(normalize(table.group(1)), set()).update(
                normalize(column) for column in column_pattern.findall(content)
            )
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
    if not SCHEMA_FILE.exists():
        STATUS_FILE.write_text(json.dumps({"schema_changed": False, "reason": "no_schema_registry"}, indent=4), encoding="utf-8")
        print(f"No schema registry found: {SCHEMA_FILE}")
        return

    schema = json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))
    covered = discovered_columns()
    generated_any = False

    for raw_table, raw_columns in sorted(schema.items()):
        table = normalize(raw_table)
        columns = [str(c).replace("\ufeff", "").strip() for c in raw_columns]
        existing = covered.get(table, set())
        new_columns = [c for c in columns if normalize(c) not in existing]
        if not new_columns:
            continue

        if not existing:
            change_id = f"mssql-create-{table}"
            body = (
                "        <preConditions onFail=\"MARK_RAN\"><not><tableExists tableName=\"%s\"/></not></preConditions>\n" % table
                + f"        <createTable tableName=\"{table}\">\n"
                + "".join(f'            <column name="{column}" type="VARCHAR(255)"/>\n' for column in columns)
                + "        </createTable>\n"
            )
        else:
            token = "-".join(normalize(c) for c in new_columns)
            change_id = f"mssql-add-{table}-{token}"
            checks = "".join(f'            <not><columnExists tableName="{table}" columnName="{column}"/></not>\n' for column in new_columns)
            body = (
                "        <preConditions onFail=\"MARK_RAN\"><and>\n" + checks + "        </and></preConditions>\n"
                + f"        <addColumn tableName=\"{table}\">\n"
                + "".join(f'            <column name="{column}" type="VARCHAR(255)"/>\n' for column in new_columns)
                + "        </addColumn>\n"
            )

        changed = write_changeset(f"{change_id}.xml", changelog(change_id, body))
        generated_any = generated_any or changed
        covered.setdefault(table, set()).update(normalize(c) for c in new_columns)

    STATUS_FILE.write_text(json.dumps({"schema_changed": generated_any}, indent=4), encoding="utf-8")
    print(f"Schema changed: {generated_any}")


if __name__ == "__main__":
    main()
