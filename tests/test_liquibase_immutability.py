import hashlib
import json
import runpy
import sys
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


def test_mysql_existing_changeset_with_different_content_fails_without_rewrite():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        (root / "metadata" / "mysql").mkdir(parents=True)
        (root / "liquibase" / "mysql").mkdir(parents=True)

        schema = {"brands": ["brand_id", "brand_name"]}
        (root / "metadata" / "mysql" / "schema_registry.json").write_text(
            json.dumps(schema), encoding="utf-8"
        )

        (root / "liquibase" / "mysql" / "mysql-create-brands.xml").write_text(
            '''<databaseChangeLog><changeSet><createTable tableName="brands"><column name="brand_id" type="VARCHAR(255)"/><column name="brand_name" type="VARCHAR(255)"/></createTable></changeSet></databaseChangeLog>''',
            encoding="utf-8",
        )
        existing_xml = "not the generated immutable definition\n"
        changeset_path = root / "liquibase" / "mysql" / "mysql-modify-brands-brand_id-varchar255-to-decimal.xml"
        changeset_path.write_text(existing_xml, encoding="utf-8")
        before_hash = _sha256(changeset_path)

        script_path = _copy_script(root, "scripts/python/mysql/setup/generate_liquibase_xml.py")

        try:
            (root / "metadata" / "mysql" / "datatype_registry.json").write_text(
                json.dumps({"brands": {"brand_id": {"final_type": "DECIMAL"}}}), encoding="utf-8"
            )
            _run_script(script_path)
        except RuntimeError as exc:
            assert "IMMUTABLE_CHANGESET_VIOLATION" in str(exc)
        else:
            raise AssertionError("expected immutable changeset violation")

        assert changeset_path.exists()
        assert _sha256(changeset_path) == before_hash
        assert changeset_path.read_text(encoding="utf-8") == existing_xml


def test_mysql_generator_is_idempotent_across_reruns():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)

        (root / "metadata" / "mysql").mkdir(parents=True)
        (root / "liquibase" / "mysql").mkdir(parents=True)

        schema = {"brands": ["brand_id", "brand_name"]}
        (root / "metadata" / "mysql" / "schema_registry.json").write_text(
            json.dumps(schema), encoding="utf-8"
        )

        script_path = _copy_script(root, "scripts/python/mysql/setup/generate_liquibase_xml.py")

        _run_script(script_path)
        generated = sorted((root / "liquibase" / "mysql").glob("*.xml"))
        assert generated
        before = {p.name: _sha256(p) for p in generated}

        _run_script(script_path)
        after = {p.name: _sha256(p) for p in sorted((root / "liquibase" / "mysql").glob("*.xml"))}

        assert before == after


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


def test_mysql_datatype_transitions_get_distinct_immutable_changesets():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "metadata" / "mysql").mkdir(parents=True)
        (root / "liquibase" / "mysql").mkdir(parents=True)
        (root / "metadata" / "mysql" / "schema_registry.json").write_text(
            json.dumps({"accounts": ["balance"]}), encoding="utf-8"
        )
        datatype_path = root / "metadata" / "mysql" / "datatype_registry.json"
        datatype_path.write_text(json.dumps({"accounts": {"balance": {"final_type": "VARCHAR(255)"}}}), encoding="utf-8")
        script_path = _copy_script(root, "scripts/python/mysql/setup/generate_liquibase_xml.py")
        _run_script(script_path)

        datatype_path.write_text(json.dumps({"accounts": {"balance": {"final_type": "DECIMAL(10,2)"}}}), encoding="utf-8")
        _run_script(script_path)
        first = root / "liquibase" / "mysql" / "mysql-modify-accounts-balance-varchar255-to-decimal102.xml"
        assert first.exists()
        first_hash = _sha256(first)

        datatype_path.write_text(json.dumps({"accounts": {"balance": {"final_type": "FLOAT"}}}), encoding="utf-8")
        _run_script(script_path)
        second = root / "liquibase" / "mysql" / "mysql-modify-accounts-balance-decimal102-to-float.xml"
        assert second.exists()
        assert _sha256(first) == first_hash

        _run_script(script_path)
        assert _sha256(first) == first_hash
        assert json.loads((root / "metadata" / "mysql" / "schema_status.json").read_text())["schema_changed"] is False


def test_mssql_generator_is_idempotent_and_new_changesets_are_semantic():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "metadata" / "mssql").mkdir(parents=True)
        (root / "liquibase" / "mssql").mkdir(parents=True)
        registry = root / "metadata" / "mssql" / "schema_registry.json"
        registry.write_text(json.dumps({"accounts": ["id"]}), encoding="utf-8")
        script_path = _copy_script(root, "scripts/python/mssql/setup/generate_liquibase_xml.py")
        _run_script(script_path)
        first = root / "liquibase" / "mssql" / "mssql-create-accounts.xml"
        first_hash = _sha256(first)
        manifest = json.loads((root / "metadata" / "mssql" / "migration_manifest.json").read_text())
        assert manifest["migrations"][0]["file"] == first.name
        _run_script(script_path)
        assert _sha256(first) == first_hash
        assert json.loads((root / "metadata" / "mssql" / "schema_status.json").read_text())["schema_changed"] is False

        registry.write_text(json.dumps({"accounts": ["id", "balance"]}), encoding="utf-8")
        _run_script(script_path)
        assert (root / "liquibase" / "mssql" / "mssql-add-accounts-balance.xml").exists()
        assert _sha256(first) == first_hash


def test_mssql_uses_registry_types_and_generates_drop_and_modify_changesets():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "metadata" / "mssql").mkdir(parents=True)
        (root / "liquibase" / "mssql").mkdir(parents=True)
        registry = root / "metadata" / "mssql" / "schema_registry.json"
        types = root / "metadata" / "mssql" / "datatype_registry.json"
        registry.write_text(json.dumps({"orders": ["id", "amount", "obsolete"]}), encoding="utf-8")
        types.write_text(json.dumps({"orders": {
            "id": {"final_type": "INTEGER"},
            "amount": {"selected_type": "VARCHAR(255)"},
            "obsolete": {"detected_type": "DATE"},
        }}), encoding="utf-8")
        script_path = _copy_script(root, "scripts/python/mssql/setup/generate_liquibase_xml.py")
        _run_script(script_path)
        create = root / "liquibase" / "mssql" / "mssql-create-orders.xml"
        create_text = create.read_text(encoding="utf-8")
        assert 'name="id" type="INTEGER"' in create_text
        assert 'name="amount" type="VARCHAR(255)"' in create_text
        assert 'name="obsolete" type="DATE"' in create_text
        create_hash = _sha256(create)

        registry.write_text(json.dumps({"orders": ["id", "amount"]}), encoding="utf-8")
        types.write_text(json.dumps({"orders": {
            "id": {"final_type": "INTEGER"},
            "amount": {"final_type": "DECIMAL(10,2)"},
        }}), encoding="utf-8")
        _run_script(script_path)
        assert (root / "liquibase" / "mssql" / "mssql-drop-orders-obsolete.xml").exists()
        modify = root / "liquibase" / "mssql" / "mssql-modify-orders-amount-varchar255-to-decimal102.xml"
        assert modify.exists()
        assert 'newDataType="DECIMAL(10,2)"' in modify.read_text(encoding="utf-8")
        assert _sha256(create) == create_hash
        modify_hash = _sha256(modify)
        types.write_text(json.dumps({"orders": {
            "id": {"final_type": "INTEGER"},
            "amount": {"final_type": "FLOAT"},
        }}), encoding="utf-8")
        _run_script(script_path)
        second_modify = root / "liquibase" / "mssql" / "mssql-modify-orders-amount-decimal102-to-float.xml"
        assert second_modify.exists()
        assert _sha256(modify) == modify_hash
        before = {path.name: _sha256(path) for path in (root / "liquibase" / "mssql").glob("*.xml")}
        _run_script(script_path)
        after = {path.name: _sha256(path) for path in (root / "liquibase" / "mssql").glob("*.xml")}
        assert before == after


def test_mssql_rename_requires_explicit_mapping_and_ambiguous_change_is_add_drop():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "metadata" / "mssql").mkdir(parents=True)
        (root / "liquibase" / "mssql").mkdir(parents=True)
        registry = root / "metadata" / "mssql" / "schema_registry.json"
        registry.write_text(json.dumps({"customers": ["customer_name"]}), encoding="utf-8")
        script_path = _copy_script(root, "scripts/python/mssql/setup/generate_liquibase_xml.py")
        _run_script(script_path)
        registry.write_text(json.dumps({"customers": ["customer_full_name"]}), encoding="utf-8")
        (root / "metadata" / "mssql" / "schema_renames.json").write_text(
            json.dumps({"customers": {"customer_name": "customer_full_name"}}), encoding="utf-8"
        )
        _run_script(script_path)
        assert (root / "liquibase" / "mssql" / "mssql-rename-customers-customer_name-customer_full_name.xml").exists()

        registry.write_text(json.dumps({"customers": ["first_name", "last_name"]}), encoding="utf-8")
        (root / "metadata" / "mssql" / "schema_renames.json").unlink()
        _run_script(script_path)
        assert (root / "liquibase" / "mssql" / "mssql-add-customers-first_name-last_name.xml").exists()
        assert (root / "liquibase" / "mssql" / "mssql-drop-customers-customer_full_name.xml").exists()


def test_mssql_applied_changeset_without_source_fails_before_generation():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        (root / "metadata" / "mssql").mkdir(parents=True)
        (root / "liquibase" / "mssql").mkdir(parents=True)
        script_path = _copy_script(root, "scripts/python/mssql/setup/generate_liquibase_xml.py")
        module = runpy.run_path(str(script_path), run_name="mssql_generator")
        try:
            module["verify_applied_history"](
                {}, [("001", "tanisha", "liquibase/mssql/001_create_sales_reconciliation.xml")]
            )
        except RuntimeError as exc:
            assert "IMMUTABLE_MIGRATION_HISTORY_MISSING" in str(exc)
            assert "mssql:001:tanisha" in str(exc)
        else:
            raise AssertionError("missing applied source artifact must fail")


def test_mysql_view_template_has_loader_contract():
    template_dir = REPO_ROOT / "scripts" / "python" / "common" / "objects"
    sys.path.insert(0, str(template_dir))
    try:
        from template_loader import load_template
        rendered = load_template("mysql", "view").format(
            view_name="v_accounts", columns="id", table_name="accounts", limit="10"
        )
    finally:
        sys.path.remove(str(template_dir))
    assert "CREATE OR REPLACE VIEW v_accounts AS" in rendered
    assert "LIMIT 10;" in rendered


def test_master_updater_is_idempotent_and_deduplicates_includes():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        directory = root / "liquibase" / "mysql"
        directory.mkdir(parents=True)
        (directory / "mysql-create-a.xml").write_text("<databaseChangeLog/>", encoding="utf-8")
        (directory / "mysql-create-b.xml").write_text("<databaseChangeLog/>", encoding="utf-8")
        master = directory / "master.xml"
        master.write_text(
            '''<?xml version="1.0"?><databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"><include file="mysql-create-a.xml" relativeToChangelogFile="true"/><include file="mysql-create-a.xml" relativeToChangelogFile="true"/></databaseChangeLog>''',
            encoding="utf-8",
        )
        script_path = _copy_script(root, "scripts/python/mysql/setup/update_master_xml.py")
        _run_script(script_path)
        first_hash = _sha256(master)
        text = master.read_text(encoding="utf-8")
        assert text.count('file="mysql-create-a.xml"') == 1
        assert text.count('file="mysql-create-b.xml"') == 1
        _run_script(script_path)
        assert _sha256(master) == first_hash


def test_mssql_master_updater_removes_only_missing_includes_and_validator_fails_clearly():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        directory = root / "liquibase" / "mssql"
        directory.mkdir(parents=True)
        valid = directory / "mssql-create-employees.xml"
        valid.write_text("<databaseChangeLog/>", encoding="utf-8")
        master = directory / "master.xml"
        master.write_text(
            '''<?xml version="1.0"?><databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"><include file="mssql-create-employees.xml" relativeToChangelogFile="true"/><include file="001_create_employees.xml" relativeToChangelogFile="true"/></databaseChangeLog>''',
            encoding="utf-8",
        )
        updater = _copy_script(root, "scripts/python/mssql/setup/update_master_xml.py")
        validator = _copy_script(root, "scripts/python/mssql/setup/validate_master_xml.py")
        _run_script(updater)
        first_hash = _sha256(master)
        text = master.read_text(encoding="utf-8")
        assert 'file="mssql-create-employees.xml"' in text
        assert "001_create_employees.xml" not in text
        _run_script(updater)
        assert _sha256(master) == first_hash

        validation = runpy.run_path(str(validator), run_name="validator")
        validation["validate_master_xml"]()
        valid.unlink()
        try:
            validation["validate_master_xml"]()
        except RuntimeError as exc:
            assert "MSSQL_CHANGELOG_INTEGRITY_ERROR" in str(exc)
            assert "mssql-create-employees.xml" in str(exc)
        else:
            raise AssertionError("expected missing changelog validation failure")
