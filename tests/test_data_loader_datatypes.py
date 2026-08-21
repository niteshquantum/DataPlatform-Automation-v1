#!/usr/bin/env python

"""
Focused tests for data_loader.py datatype integration.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.data_loader import (
    _load_datatype_registry,
    _build_column_types,
    create_table,
    add_missing_columns,
    load_and_insert_file,
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
                "selected_type": "TEXT",
            },
            "is_active": {
                "detected_type": "BOOLEAN",
                "selected_type": "BOOLEAN",
            },
        }
    }


# ============================================================
# TEST A — MySQL selected BIGINT creates BIGINT
# ============================================================

def test_mysql_create_table_with_bigint():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    column_names = ["customer_id", "first_name"]
    column_types = {"customer_id": "BIGINT", "first_name": "TEXT"}

    create_table(conn, "mysql", "customers", column_names, column_types)

    assert cursor.execute.called
    sql = cursor.execute.call_args[0][0]
    assert "`customer_id` BIGINT" in sql
    assert "`first_name` TEXT" in sql
    assert "VARCHAR(255)" not in sql


# ============================================================
# TEST B — PostgreSQL selected INTEGER creates INTEGER
# ============================================================

def test_postgresql_create_table_with_integer():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    column_names = ["customer_id"]
    column_types = {"customer_id": "INTEGER"}

    create_table(conn, "postgresql", "customers", column_names, column_types)

    assert cursor.execute.called
    sql = cursor.execute.call_args[0][0]
    assert '"customer_id" INTEGER' in sql
    assert "VARCHAR(255)" not in sql


# ============================================================
# TEST C — MSSQL selected BOOLEAN creates BIT
# ============================================================

def test_mssql_create_table_with_bit():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    column_names = ["is_active"]
    column_types = {"is_active": "BIT"}

    create_table(conn, "mssql", "customers", column_names, column_types)

    assert cursor.execute.called
    sql = cursor.execute.call_args[0][0]
    assert "[is_active] BIT" in sql
    assert "VARCHAR(255)" not in sql


# ============================================================
# TEST D — selected_type overrides detected_type
# ============================================================

def test_selected_type_overrides_detected_type():
    registry = sample_registry()
    types = _build_column_types("customers", ["customer_id"], "mysql", registry)
    assert types["customer_id"] == "BIGINT"


# ============================================================
# TEST E — missing selected_type uses detected_type
# ============================================================

def test_missing_selected_type_uses_detected_type():
    registry = {
        "customers": {
            "customer_id": {
                "detected_type": "INTEGER",
            }
        }
    }
    types = _build_column_types("customers", ["customer_id"], "mysql", registry)
    assert types["customer_id"] == "INT"


# ============================================================
# TEST F — missing datatype_registry preserves VARCHAR(255)
# ============================================================

def test_missing_datatype_registry_preserves_varchar():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    column_names = ["customer_id", "first_name"]

    create_table(conn, "mysql", "customers", column_names, column_types=None)

    assert cursor.execute.called
    sql = cursor.execute.call_args[0][0]
    assert "`customer_id` VARCHAR(255)" in sql
    assert "`first_name` VARCHAR(255)" in sql


# ============================================================
# TEST G — CREATE TABLE uses resolved datatype
# ============================================================

def test_create_table_uses_resolved_datatype():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    column_names = ["customer_id", "first_name"]
    column_types = {"customer_id": "BIGINT", "first_name": "TEXT"}

    create_table(conn, "mysql", "customers", column_names, column_types)

    sql = cursor.execute.call_args[0][0]
    assert "`customer_id` BIGINT" in sql
    assert "`first_name` TEXT" in sql


# ============================================================
# TEST H — ADD COLUMN uses resolved datatype
# ============================================================

def test_add_column_uses_resolved_datatype():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    missing_columns = ["email"]
    column_types = {"email": "VARCHAR(255)"}

    add_missing_columns(conn, "postgresql", "customers", missing_columns, column_types)

    assert cursor.execute.called
    sql = cursor.execute.call_args[0][0]
    assert '"email" VARCHAR(255)' in sql


# ============================================================
# TEST I — target table/column mapping still works
# ============================================================

def test_target_names_preserved():
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    column_names = ["customer_id", "first_name", "last_name"]
    column_types = {
        "customer_id": "BIGINT",
        "first_name": "TEXT",
        "last_name": "TEXT",
    }

    create_table(conn, "mysql", "customers", column_names, column_types)

    sql = cursor.execute.call_args[0][0]
    assert "customers" in sql
    assert "customer_id" in sql
    assert "first_name" in sql
    assert "last_name" in sql


# ============================================================
# TEST J — existing row insertion still works
# ============================================================

def test_insert_rows_unchanged():
    from scripts.data_loader import insert_rows

    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor

    rows = [
        {"customer_id": "1", "first_name": "John"},
        {"customer_id": "2", "first_name": "Jane"},
    ]
    actual_columns = ["customer_id", "first_name"]

    inserted = insert_rows(conn, "mysql", "customers", actual_columns, rows)

    assert inserted == 2
    assert cursor.executemany.called


# ============================================================
# TEST — load_and_insert_file with mock DB
# ============================================================

def test_load_and_insert_file_uses_resolved_types():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    mock_cursor.fetchall.return_value = []

    mock_path = MagicMock()
    mock_path.suffix = ".csv"
    mock_path.stem = "Customer Records"
    mock_path.name = "Customer Records.csv"

    csv_content = "CustomerID,FirstName,LastName\n1,John,Doe\n"

    sample_reg = {
        "customers": {
            "customer_id": {"detected_type": "INTEGER", "selected_type": "BIGINT"},
            "first_name": {"detected_type": "TEXT", "selected_type": "TEXT"},
            "last_name": {"detected_type": "TEXT", "selected_type": "TEXT"},
        }
    }

    with patch("scripts.data_loader.read_csv_file", return_value=[
        {"CustomerID": "1", "FirstName": "John", "LastName": "Doe"}
    ]):
        with patch("scripts.data_loader.get_table_columns", return_value=[]):
            with patch("scripts.data_loader.create_table") as mock_create:
                with patch("scripts.data_loader.prepare_rows") as mock_prepare:
                    with patch("scripts.data_loader.insert_rows", return_value=1):
                        with patch("scripts.data_loader._load_datatype_registry", return_value=sample_reg):
                            mock_prepare.return_value = [["1", "John", "Doe"]]

                            result = load_and_insert_file(
                                mock_conn, "mysql", mock_path
                            )

    assert result == 1
    assert mock_create.called
    call_args = mock_create.call_args[0]
    assert len(call_args) == 5  # conn, db_type, table_name, column_names, column_types
    column_types = call_args[4]
    assert column_types["customer_id"] == "BIGINT"
    assert column_types["first_name"] == "TEXT"
    assert column_types["last_name"] == "TEXT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
