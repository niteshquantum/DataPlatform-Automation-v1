#!/usr/bin/env python

"""
Focused tests for migration generate_ddl.py datatype integration.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    PROJECT_ROOT / "scripts" / "python" / "migration" / "generate_ddl.py"
)
METADATA_BASE = PROJECT_ROOT / "metadata"
LIQUIBASE_BASE = PROJECT_ROOT / "liquibase" / "migration"

DATABASES = ["mysql", "postgresql", "mssql"]
METADATA_FILES = ["schema_registry.json", "datatype_registry.json", "schema_status.json"]


def run_generator(db_type):
    env = {
        **dict(__import__('os').environ),
        "PYTHONPATH": str(PROJECT_ROOT),
        "DESTINATION_DATABASE": db_type,
    }
    result = subprocess.run(
        [sys.executable, str(GENERATOR_PATH)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env=env,
    )
    return result


def find_generated_xml(db_type):
    dir_path = LIQUIBASE_BASE / db_type
    return sorted(
        f for f in dir_path.glob("*.xml")
        if f.name not in ("master.xml", "master_objects.xml")
    )


def _backup_metadata(db_type):
    backup = {}
    for fname in METADATA_FILES:
        p = METADATA_BASE / db_type / fname
        if p.exists():
            backup[fname] = p.read_text(encoding="utf-8")
        else:
            backup[fname] = None
    return backup


def _restore_metadata(db_type, backup):
    for fname, content in backup.items():
        p = METADATA_BASE / db_type / fname
        if content is not None:
            p.write_text(content, encoding="utf-8")
        elif p.exists():
            p.unlink()


def _cleanup_liquibase(db_type):
    dir_path = LIQUIBASE_BASE / db_type
    for f in dir_path.glob("*.xml"):
        if f.name not in ("master.xml", "master_objects.xml"):
            f.unlink()
    master_objects = dir_path / "master_objects.xml"
    if master_objects.exists():
        master_objects.unlink()


# ============================================================
# TEST A — MySQL selected BIGINT → BIGINT
# ============================================================

def test_mysql_selected_bigint():
    db_type = "mysql"
    backup = _backup_metadata(db_type)
    try:
        schema = {"test_customers": ["customer_id", "first_name"]}
        datatype = {
            "test_customers": {
                "customer_id": {"detected_type": "INTEGER", "selected_type": "BIGINT"},
                "first_name": {"detected_type": "TEXT", "selected_type": "TEXT"},
            }
        }
        with open(METADATA_BASE / db_type / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)
        with open(METADATA_BASE / db_type / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype, f)

        result = run_generator(db_type)
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml(db_type)
        assert len(xml_files) == 1
        content = xml_files[0].read_text(encoding="utf-8")
        assert 'type="BIGINT"' in content
        assert 'type="TEXT"' in content
        assert "VARCHAR(255)" not in content
    finally:
        _cleanup_liquibase(db_type)
        _restore_metadata(db_type, backup)


# ============================================================
# TEST B — PostgreSQL selected INTEGER → INTEGER
# ============================================================

def test_postgresql_selected_integer():
    db_type = "postgresql"
    backup = _backup_metadata(db_type)
    try:
        schema = {"test_customers": ["customer_id"]}
        datatype = {
            "test_customers": {
                "customer_id": {"detected_type": "INTEGER", "selected_type": "INTEGER"},
            }
        }
        with open(METADATA_BASE / db_type / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)
        with open(METADATA_BASE / db_type / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype, f)

        result = run_generator(db_type)
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml(db_type)
        assert len(xml_files) == 1
        content = xml_files[0].read_text(encoding="utf-8")
        assert 'type="INTEGER"' in content
        assert "VARCHAR(255)" not in content
    finally:
        _cleanup_liquibase(db_type)
        _restore_metadata(db_type, backup)


# ============================================================
# TEST C — MSSQL selected BOOLEAN → BIT
# ============================================================

def test_mssql_selected_boolean():
    db_type = "mssql"
    backup = _backup_metadata(db_type)
    try:
        schema = {"test_customers": ["is_active"]}
        datatype = {
            "test_customers": {
                "is_active": {"detected_type": "BOOLEAN", "selected_type": "BOOLEAN"},
            }
        }
        with open(METADATA_BASE / db_type / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)
        with open(METADATA_BASE / db_type / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype, f)

        result = run_generator(db_type)
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml(db_type)
        assert len(xml_files) == 1
        content = xml_files[0].read_text(encoding="utf-8")
        assert 'type="BIT"' in content
        assert "VARCHAR(255)" not in content
    finally:
        _cleanup_liquibase(db_type)
        _restore_metadata(db_type, backup)


# ============================================================
# TEST D — selected_type overrides detected_type
# ============================================================

def test_selected_type_overrides_detected_type():
    db_type = "mysql"
    backup = _backup_metadata(db_type)
    try:
        schema = {"test_customers": ["customer_id"]}
        datatype = {
            "test_customers": {
                "customer_id": {"detected_type": "INTEGER", "selected_type": "BIGINT"},
            }
        }
        with open(METADATA_BASE / db_type / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)
        with open(METADATA_BASE / db_type / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype, f)

        result = run_generator(db_type)
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml(db_type)
        assert len(xml_files) == 1
        content = xml_files[0].read_text(encoding="utf-8")
        assert 'type="BIGINT"' in content
    finally:
        _cleanup_liquibase(db_type)
        _restore_metadata(db_type, backup)


# ============================================================
# TEST E — missing selected_type uses detected_type
# ============================================================

def test_missing_selected_type_uses_detected_type():
    db_type = "postgresql"
    backup = _backup_metadata(db_type)
    try:
        schema = {"test_customers": ["customer_id"]}
        datatype = {
            "test_customers": {
                "customer_id": {"detected_type": "INTEGER"},
            }
        }
        with open(METADATA_BASE / db_type / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)
        with open(METADATA_BASE / db_type / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype, f)

        result = run_generator(db_type)
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml(db_type)
        assert len(xml_files) == 1
        content = xml_files[0].read_text(encoding="utf-8")
        assert 'type="INTEGER"' in content
    finally:
        _cleanup_liquibase(db_type)
        _restore_metadata(db_type, backup)


# ============================================================
# TEST F — missing datatype_registry preserves VARCHAR(255)
# ============================================================

def test_missing_datatype_registry_falls_back_to_varchar():
    db_type = "mssql"
    backup = _backup_metadata(db_type)
    try:
        schema = {"test_customers": ["customer_id"]}
        with open(METADATA_BASE / db_type / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)

        datatype_path = METADATA_BASE / db_type / "datatype_registry.json"
        if datatype_path.exists():
            datatype_path.unlink()

        result = run_generator(db_type)
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml(db_type)
        assert len(xml_files) == 1
        content = xml_files[0].read_text(encoding="utf-8")
        assert 'type="VARCHAR(255)"' in content
    finally:
        _cleanup_liquibase(db_type)
        _restore_metadata(db_type, backup)


# ============================================================
# TEST G — CREATE TABLE uses resolved datatype
# ============================================================

def test_create_table_uses_resolved_datatype():
    db_type = "mysql"
    backup = _backup_metadata(db_type)
    try:
        schema = {"test_customers": ["customer_id", "first_name"]}
        datatype = {
            "test_customers": {
                "customer_id": {"detected_type": "INTEGER", "selected_type": "BIGINT"},
                "first_name": {"detected_type": "TEXT", "selected_type": "VARCHAR"},
            }
        }
        with open(METADATA_BASE / db_type / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)
        with open(METADATA_BASE / db_type / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype, f)

        result = run_generator(db_type)
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml(db_type)
        assert len(xml_files) == 1
        content = xml_files[0].read_text(encoding="utf-8")
        assert 'type="BIGINT"' in content
        assert 'type="VARCHAR(255)"' in content
    finally:
        _cleanup_liquibase(db_type)
        _restore_metadata(db_type, backup)


# ============================================================
# TEST H — ADD COLUMN uses resolved datatype
# ============================================================

def test_add_column_uses_resolved_datatype():
    db_type = "postgresql"
    backup = _backup_metadata(db_type)
    try:
        schema = {"test_customers": ["customer_id", "email"]}
        datatype = {
            "test_customers": {
                "customer_id": {"detected_type": "INTEGER", "selected_type": "INTEGER"},
                "email": {"detected_type": "TEXT", "selected_type": "VARCHAR"},
            }
        }
        with open(METADATA_BASE / db_type / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)
        with open(METADATA_BASE / db_type / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype, f)

        # Pre-create a changeset XML that covers customer_id
        # so the next run only adds email via addColumn
        covered_xml = LIQUIBASE_BASE / db_type / "001_create_test_customers.xml"
        covered_xml.parent.mkdir(parents=True, exist_ok=True)
        covered_xml.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"\n'
            '        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
            '        xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog\n'
            '        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">\n'
            '    <changeSet id="001" author="tanisha">\n'
            '        <createTable tableName="test_customers">\n'
            '            <column name="customer_id" type="INTEGER"/>\n'
            '        </createTable>\n'
            '    </changeSet>\n'
            '</databaseChangeLog>\n',
            encoding="utf-8"
        )

        result = run_generator(db_type)
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml(db_type)
        alter_files = [f for f in xml_files if "alter" in f.name]
        assert len(alter_files) == 1
        content = alter_files[0].read_text(encoding="utf-8")
        assert 'type="VARCHAR(255)"' in content
    finally:
        _cleanup_liquibase(db_type)
        _restore_metadata(db_type, backup)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
