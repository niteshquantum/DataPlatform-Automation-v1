#!/usr/bin/env python

"""
Focused tests for the generic datatype resolver.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest

from scripts.python.common.datatype_resolver import (
    load_datatype_registry,
    map_to_physical_type,
    resolve_logical_type,
    resolve_column_type,
    get_column_type,
    UnsupportedDatabaseError,
    UnsupportedTypeError,
    MissingConfigError,
)


# ============================================================
# HELPERS
# ============================================================

def sample_registry():
    return {
        "customers": {
            "customer_id": {
                "detected_type": "INTEGER",
                "selected_type": "BIGINT",
            },
            "first_name": {
                "detected_type": "TEXT",
                "selected_type": "VARCHAR",
            },
            "is_active": {
                "detected_type": "BOOLEAN",
                "selected_type": "BOOLEAN",
            },
            "price": {
                "detected_type": "NUMERIC",
                "selected_type": "NUMERIC",
            },
            "created_at": {
                "detected_type": "TIMESTAMP",
                "selected_type": "TIMESTAMP",
            },
        },
        "fallback_table": {
            "col_with_selected": {
                "selected_type": "DATE",
            },
            "col_with_detected_only": {
                "detected_type": "TEXT",
            },
            "col_empty_selected": {
                "detected_type": "INTEGER",
                "selected_type": "",
            },
            "col_null_selected": {
                "detected_type": "INTEGER",
                "selected_type": "null",
            },
            "col_missing_both": {},
        },
    }


# ============================================================
# MYSQL MAPPING TESTS
# ============================================================

@pytest.mark.parametrize("logical,expected", [
    ("INTEGER", "INT"),
    ("integer", "INT"),
    ("Integer", "INT"),
    ("BIGINT", "BIGINT"),
    ("NUMERIC", "DECIMAL(18,4)"),
    ("TEXT", "TEXT"),
    ("VARCHAR", "VARCHAR(255)"),
    ("DATE", "DATE"),
    ("TIMESTAMP", "TIMESTAMP"),
    ("BOOLEAN", "BOOLEAN"),
])
def test_mysql_mapping(logical, expected):
    assert map_to_physical_type(logical, "mysql") == expected


# ============================================================
# POSTGRESQL MAPPING TESTS
# ============================================================

@pytest.mark.parametrize("logical,expected", [
    ("INTEGER", "INTEGER"),
    ("integer", "INTEGER"),
    ("Integer", "INTEGER"),
    ("BIGINT", "BIGINT"),
    ("NUMERIC", "NUMERIC"),
    ("TEXT", "TEXT"),
    ("VARCHAR", "VARCHAR(255)"),
    ("DATE", "DATE"),
    ("TIMESTAMP", "TIMESTAMP"),
    ("BOOLEAN", "BOOLEAN"),
])
def test_postgresql_mapping(logical, expected):
    assert map_to_physical_type(logical, "postgresql") == expected


# ============================================================
# MSSQL MAPPING TESTS
# ============================================================

@pytest.mark.parametrize("logical,expected", [
    ("INTEGER", "INT"),
    ("integer", "INT"),
    ("Integer", "INT"),
    ("BIGINT", "BIGINT"),
    ("NUMERIC", "DECIMAL(18,4)"),
    ("TEXT", "NVARCHAR(MAX)"),
    ("VARCHAR", "NVARCHAR(255)"),
    ("DATE", "DATE"),
    ("TIMESTAMP", "DATETIME2"),
    ("BOOLEAN", "BIT"),
])
def test_mssql_mapping(logical, expected):
    assert map_to_physical_type(logical, "mssql") == expected


# ============================================================
# RESOLUTION PRECEDENCE TESTS
# ============================================================

def test_selected_type_overrides_detected_type():
    registry = sample_registry()
    assert resolve_logical_type("customers", "customer_id", registry) == "BIGINT"


def test_selected_type_wins_over_detected_type():
    registry = sample_registry()
    assert resolve_logical_type("customers", "first_name", registry) == "VARCHAR"


def test_detected_type_used_when_selected_missing():
    registry = sample_registry()
    assert resolve_logical_type("fallback_table", "col_with_detected_only", registry) == "TEXT"


def test_empty_selected_falls_back_to_detected():
    registry = sample_registry()
    assert resolve_logical_type("fallback_table", "col_empty_selected", registry) == "INTEGER"


def test_null_selected_falls_back_to_detected():
    registry = sample_registry()
    assert resolve_logical_type("fallback_table", "col_null_selected", registry) == "INTEGER"


def test_missing_both_returns_default():
    registry = sample_registry()
    result = resolve_logical_type("fallback_table", "col_missing_both", registry)
    assert result == "TEXT"


# ============================================================
# CASE NORMALIZATION TESTS
# ============================================================

def test_db_case_normalization():
    assert map_to_physical_type("INTEGER", "mysql") == "INT"
    assert map_to_physical_type("INTEGER", "MYSQL") == "INT"
    assert map_to_physical_type("INTEGER", "MySQL") == "INT"


def test_logical_type_case_normalization():
    assert map_to_physical_type("integer", "mysql") == "INT"
    assert map_to_physical_type("Integer", "mysql") == "INT"
    assert map_to_physical_type("INTEGER", "mysql") == "INT"


# ============================================================
# ERROR TESTS
# ============================================================

def test_unsupported_database():
    with pytest.raises(UnsupportedDatabaseError):
        map_to_physical_type("INTEGER", "mongodb")


def test_unsupported_logical_type():
    with pytest.raises(UnsupportedTypeError):
        map_to_physical_type("UUID", "mysql")


def test_missing_config(monkeypatch):
    import scripts.python.common.datatype_resolver as dr
    monkeypatch.setattr(dr, "_CONFIG_PATH", Path("/nonexistent/datatype_rules.json"))
    with pytest.raises(MissingConfigError):
        load_datatype_registry("mysql")


def test_column_not_found_in_registry():
    registry = sample_registry()
    with pytest.raises(ValueError):
        resolve_logical_type("customers", "nonexistent_col", registry)


def test_table_not_found_in_registry():
    registry = sample_registry()
    with pytest.raises(ValueError):
        resolve_logical_type("nonexistent_table", "col", registry)


# ============================================================
# RESOLVE COLUMN TYPE TESTS
# ============================================================

def test_resolve_column_type_selected_overrides():
    registry = sample_registry()
    assert resolve_column_type("customers", "customer_id", "mysql", registry) == "BIGINT"
    assert resolve_column_type("customers", "customer_id", "postgresql", registry) == "BIGINT"
    assert resolve_column_type("customers", "customer_id", "mssql", registry) == "BIGINT"


def test_resolve_column_type_fallback():
    registry = sample_registry()
    assert resolve_column_type("fallback_table", "col_with_detected_only", "mysql", registry) == "TEXT"
    assert resolve_column_type("fallback_table", "col_with_detected_only", "postgresql", registry) == "TEXT"
    assert resolve_column_type("fallback_table", "col_with_detected_only", "mssql", registry) == "NVARCHAR(MAX)"


def test_get_column_type_helper():
    registry = sample_registry()
    assert get_column_type(registry, "customers", "first_name", "mysql") == "VARCHAR(255)"
    assert get_column_type(registry, "customers", "first_name", "postgresql") == "VARCHAR(255)"
    assert get_column_type(registry, "customers", "first_name", "mssql") == "NVARCHAR(255)"


# ============================================================
# LOAD DATATYPE REGISTRY TESTS
# ============================================================

def test_load_datatype_registry_returns_normalized_keys():
    registry = load_datatype_registry("mysql")
    assert "INTEGER" in registry
    assert "BIGINT" in registry
    assert "NUMERIC" in registry
    assert "TEXT" in registry
    assert "VARCHAR" in registry
    assert "DATE" in registry
    assert "TIMESTAMP" in registry
    assert "BOOLEAN" in registry


def test_load_datatype_registry_case_insensitive():
    registry = load_datatype_registry("MYSQL")
    assert "INTEGER" in registry
    assert registry["INTEGER"] == "INT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
