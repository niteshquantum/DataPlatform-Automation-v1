import hashlib
import json
import runpy
import shutil
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _copy_script(temp_root: Path, relative_script: str) -> Path:
    src = REPO_ROOT / relative_script
    dst = temp_root / relative_script
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run_script(path: Path):
    runpy.run_path(str(path), run_name="__main__")


def test_mysql_existing_changeset_is_immutable():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        (root / "metadata" / "mysql").mkdir(parents=True)
        (root / "liquibase" / "mysql").mkdir(parents=True)

        schema = {"brands": ["brand_id", "brand_name"]}
        (root / "metadata" / "mysql" / "schema_registry.json").write_text(
            json.dumps(schema), encoding="utf-8"
        )

        existing_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">
    <changeSet id="mysql-create-brands" author="tanisha">
        <preConditions onFail="MARK_RAN">
            <not><tableExists tableName="brands"/></not>
        </preConditions>
        <createTable tableName="brands">
        <column name="brand_id" type="INTEGER"/>
        <column name="brand_name" type="VARCHAR(255)"/>
        </createTable>
    </changeSet>
</databaseChangeLog>
'''
        changeset_path = root / "liquibase" / "mysql" / "mysql-create-brands.xml"
        changeset_path.write_text(existing_xml, encoding="utf-8")

        script_path = _copy_script(root, "scripts/python/mysql/setup/generate_liquibase_xml.py")

        _run_script(script_path)

        assert changeset_path.exists()
        assert changeset_path.read_text(encoding="utf-8") == existing_xml


def test_mssql_existing_changeset_is_not_deleted_for_unchanged_schema():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        (root / "metadata" / "mssql").mkdir(parents=True)
        (root / "liquibase" / "mssql").mkdir(parents=True)

        schema = {"brands": ["brand_id", "brand_name"]}
        (root / "metadata" / "mssql" / "schema_registry.json").write_text(
            json.dumps(schema), encoding="utf-8"
        )

        existing_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">
    <changeSet id="001" author="tanisha">
        <createTable tableName="brands">
            <column name="brand_id" type="VARCHAR(255)"/>
            <column name="brand_name" type="VARCHAR(255)"/>
        </createTable>
    </changeSet>
</databaseChangeLog>
'''

        changeset_path = root / "liquibase" / "mssql" / "001_create_brands.xml"
        changeset_path.write_text(existing_xml, encoding="utf-8")
        before_hash = _sha256(changeset_path)

        script_path = _copy_script(root, "scripts/python/mssql/setup/generate_liquibase_xml.py")

        _run_script(script_path)

        assert changeset_path.exists(), "existing changeset should not be deleted"
        assert _sha256(changeset_path) == before_hash
