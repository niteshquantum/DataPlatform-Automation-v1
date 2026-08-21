#!/usr/bin/env python

"""
Focused tests for PostgreSQL Liquibase datatype integration.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    PROJECT_ROOT / "scripts" / "python" / "postgresql" / "setup" / "generate_liquibase_xml.py"
)
METADATA_DIR = PROJECT_ROOT / "metadata" / "postgresql"
LIQUIBASE_DIR = PROJECT_ROOT / "liquibase" / "postgresql"

METADATA_FILES = [
    "schema_registry.json",
    "datatype_registry.json",
    "schema_status.json",
]


def run_generator():
    env = {
        **dict(__import__('os').environ),
        "PYTHONPATH": str(PROJECT_ROOT),
    }
    result = subprocess.run(
        [sys.executable, str(GENERATOR_PATH)],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
        env=env,
    )
    return result


def find_generated_xml():
    return sorted(
        f for f in LIQUIBASE_DIR.glob("*.xml")
        if f.name != "master.xml"
    )


def _backup_metadata():
    backup = {}
    for fname in METADATA_FILES:
        p = METADATA_DIR / fname
        if p.exists():
            backup[fname] = p.read_text(encoding="utf-8")
        else:
            backup[fname] = None
    return backup


def _restore_metadata(backup):
    for fname, content in backup.items():
        p = METADATA_DIR / fname
        if content is not None:
            p.write_text(content, encoding="utf-8")
        elif p.exists():
            p.unlink()


def _cleanup_liquibase():
    for f in LIQUIBASE_DIR.glob("*.xml"):
        if f.name != "master.xml":
            f.unlink()


# ============================================================
# TEST A — selected_type overrides detected_type
# ============================================================

def test_selected_type_overrides_detected_type():
    backup = _backup_metadata()
    try:
        schema = {
            "test_customers": ["customer_id", "first_name", "last_name"]
        }
        datatype = {
            "test_customers": {
                "customer_id": {
                    "detected_type": "INTEGER",
                    "selected_type": "BIGINT",
                },
                "first_name": {
                    "detected_type": "TEXT",
                    "selected_type": "TEXT",
                },
                "last_name": {
                    "detected_type": "TEXT",
                    "selected_type": "TEXT",
                },
            }
        }

        with open(METADATA_DIR / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)
        with open(METADATA_DIR / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype, f)

        result = run_generator()
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml()
        assert len(xml_files) == 1

        content = xml_files[0].read_text(encoding="utf-8")
        assert 'type="BIGINT"' in content
        assert 'type="TEXT"' in content
        assert "VARCHAR(255)" not in content
    finally:
        _cleanup_liquibase()
        _restore_metadata(backup)


# ============================================================
# TEST B — missing datatype_registry falls back to VARCHAR(255)
# ============================================================

def test_missing_datatype_registry_falls_back_to_varchar():
    backup = _backup_metadata()
    try:
        schema = {
            "test_customers": ["customer_id"]
        }

        with open(METADATA_DIR / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)

        datatype_path = METADATA_DIR / "datatype_registry.json"
        if datatype_path.exists():
            datatype_path.unlink()

        result = run_generator()
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml()
        assert len(xml_files) == 1

        content = xml_files[0].read_text(encoding="utf-8")
        assert 'type="VARCHAR(255)"' in content
    finally:
        _cleanup_liquibase()
        _restore_metadata(backup)


# ============================================================
# TEST C — detected_type used when selected_type is missing
# ============================================================

def test_detected_type_used_when_selected_type_missing():
    backup = _backup_metadata()
    try:
        schema = {
            "test_customers": ["customer_id"]
        }
        datatype = {
            "test_customers": {
                "customer_id": {
                    "detected_type": "INTEGER",
                }
            }
        }

        with open(METADATA_DIR / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)
        with open(METADATA_DIR / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype, f)

        result = run_generator()
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml()
        assert len(xml_files) == 1

        content = xml_files[0].read_text(encoding="utf-8")
        assert 'type="INTEGER"' in content
        assert "VARCHAR(255)" not in content
    finally:
        _cleanup_liquibase()
        _restore_metadata(backup)


# ============================================================
# TEST D — empty selected_type falls back to detected_type
# ============================================================

def test_empty_selected_type_falls_back_to_detected():
    backup = _backup_metadata()
    try:
        schema = {
            "test_customers": ["customer_id"]
        }
        datatype = {
            "test_customers": {
                "customer_id": {
                    "detected_type": "TEXT",
                    "selected_type": "",
                }
            }
        }

        with open(METADATA_DIR / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)
        with open(METADATA_DIR / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype, f)

        result = run_generator()
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml()
        assert len(xml_files) == 1

        content = xml_files[0].read_text(encoding="utf-8")
        assert 'type="TEXT"' in content
        assert "VARCHAR(255)" not in content
    finally:
        _cleanup_liquibase()
        _restore_metadata(backup)


# ============================================================
# TEST E — VARCHAR resolves to VARCHAR(255)
# ============================================================

def test_varchar_resolves_to_varchar_255():
    backup = _backup_metadata()
    try:
        schema = {
            "test_customers": ["first_name"]
        }
        datatype = {
            "test_customers": {
                "first_name": {
                    "detected_type": "TEXT",
                    "selected_type": "VARCHAR",
                }
            }
        }

        with open(METADATA_DIR / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema, f)
        with open(METADATA_DIR / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype, f)

        result = run_generator()
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml()
        assert len(xml_files) == 1

        content = xml_files[0].read_text(encoding="utf-8")
        assert 'type="VARCHAR(255)"' in content
    finally:
        _cleanup_liquibase()
        _restore_metadata(backup)


# ============================================================
# TEST F — addColumn branch also uses resolved types
# ============================================================

def test_add_column_branch_uses_resolved_types():
    backup = _backup_metadata()
    try:
        # First create the table
        schema_create = {
            "test_customers": ["customer_id"]
        }
        datatype_create = {
            "test_customers": {
                "customer_id": {
                    "detected_type": "INTEGER",
                    "selected_type": "INTEGER",
                }
            }
        }

        with open(METADATA_DIR / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema_create, f)
        with open(METADATA_DIR / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype_create, f)

        result = run_generator()
        assert result.returncode == 0, result.stderr

        # Now add a new column
        schema_alter = {
            "test_customers": ["customer_id", "email"]
        }
        datatype_alter = {
            "test_customers": {
                "customer_id": {
                    "detected_type": "INTEGER",
                    "selected_type": "INTEGER",
                },
                "email": {
                    "detected_type": "TEXT",
                    "selected_type": "VARCHAR",
                }
            }
        }

        with open(METADATA_DIR / "schema_registry.json", "w", encoding="utf-8") as f:
            json.dump(schema_alter, f)
        with open(METADATA_DIR / "datatype_registry.json", "w", encoding="utf-8") as f:
            json.dump(datatype_alter, f)

        result = run_generator()
        assert result.returncode == 0, result.stderr

        xml_files = find_generated_xml()
        assert len(xml_files) == 2  # create + alter

        alter_files = [f for f in xml_files if "alter" in f.name]
        assert len(alter_files) == 1

        content = alter_files[0].read_text(encoding="utf-8")
        assert 'type="VARCHAR(255)"' in content
    finally:
        _cleanup_liquibase()
        _restore_metadata(backup)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
