"""Fail closed when the persistent MSSQL schema diverges from Liquibase history."""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.mssql.setup.generate_liquibase_xml import (
    applied_changesets,
    effective_repository_schema,
    source_changesets,
    verify_applied_history,
)


def canonical_type(value):
    """Return a precise MSSQL storage-type comparison key.

    Source metadata uses portable Liquibase names (for example INTEGER and
    TIMESTAMP), whereas SQL Server catalogues report MSSQL names.  Only known
    SQL Server/Liquibase equivalents are folded; all explicit parameters stay
    part of the key so drift detection remains strict.
    """
    text = "".join(str(value).upper().split())
    match = re.fullmatch(r"([A-Z0-9_]+)(?:\(([^()]*)\))?", text)
    if not match:
        return text
    base, parameters = match.groups()
    if base == "TEXT":
        return "VARCHAR(MAX)"
    if base == "INTEGER":
        return "INT"
    if base == "NUMERIC":
        base = "DECIMAL"
    # The source detector's TIMESTAMP means a date/time value.  Liquibase maps
    # that portable expectation to DATETIME2(7) on MSSQL.  Actual SQL Server
    # TIMESTAMP/ROWVERSION is represented as ROWVERSION by _actual_type(), so
    # it is never confused with this date/time expectation.
    if base == "TIMESTAMP":
        return "DATETIME2(7)"
    if base in {"DECIMAL", "DATETIME2"} and parameters is None:
        parameters = "18,0" if base == "DECIMAL" else "7"
    return f"{base}({parameters})" if parameters is not None else base


def _actual_type(type_name, max_length, precision, scale):
    name = str(type_name).upper()
    if name in {"TIMESTAMP", "ROWVERSION"}:
        return "ROWVERSION"
    if name in {"VARCHAR", "CHAR", "VARBINARY", "BINARY"}:
        return f"{name}(MAX)" if max_length == -1 else f"{name}({max_length})"
    if name in {"NVARCHAR", "NCHAR"}:
        return f"{name}(MAX)" if max_length == -1 else f"{name}({max_length // 2})"
    if name in {"DECIMAL", "NUMERIC"}:
        return f"DECIMAL({precision},{scale})"
    if name in {"DATETIME2", "DATETIMEOFFSET", "TIME"}:
        return f"{name}({scale})"
    return name


def actual_schema(connection):
    cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT t.name, c.name, ty.name, c.max_length, c.precision, c.scale
            FROM sys.tables t
            JOIN sys.schemas s ON s.schema_id = t.schema_id
            JOIN sys.columns c ON c.object_id = t.object_id
            JOIN sys.types ty ON ty.user_type_id = c.user_type_id
            WHERE t.is_ms_shipped = 0 AND s.name = 'dbo'
              AND t.name NOT IN ('DATABASECHANGELOG', 'DATABASECHANGELOGLOCK')
            ORDER BY t.name, c.column_id
        """)
        result = {}
        for table, column, name, length, precision, scale in cursor.fetchall():
            result.setdefault(str(table).lower(), {})[str(column).lower()] = {
                "name": str(column), "type": _actual_type(name, int(length), int(precision), int(scale)),
            }
        return result
    finally:
        cursor.close()


def schema_differences(expected, actual):
    differences = []
    for table in sorted(set(expected) - set(actual)):
        differences.append(f"{table}: Expected table exists; Actual: missing")
    for table in sorted(set(actual) - set(expected)):
        differences.append(f"{table}: Expected: no table; Actual: unexpected table")
    for table in sorted(set(expected) & set(actual)):
        expected_columns, actual_columns = expected[table], actual[table]
        for column in sorted(set(expected_columns) - set(actual_columns)):
            differences.append(f"{table}.{expected_columns[column]['name']}: Expected: {expected_columns[column]['type']}; Actual: missing")
        for column in sorted(set(actual_columns) - set(expected_columns)):
            differences.append(f"{table}.{actual_columns[column]['name']}: Expected: no column; Actual: unexpected column {actual_columns[column]['type']}")
        for column in sorted(set(expected_columns) & set(actual_columns)):
            wanted, found = expected_columns[column]["type"], actual_columns[column]["type"]
            if canonical_type(wanted) != canonical_type(found):
                differences.append(f"{table}.{expected_columns[column]['name']}: Expected: {wanted}; Actual: {found}")
    return differences


def validate(mode):
    # Importing the pure comparison helpers must not require a live ODBC
    # installation; connection setup is needed only for the executable path.
    from scripts.python.mssql.setup.db_connection import get_connection
    source = source_changesets()
    applied = applied_changesets()
    verify_applied_history(source, applied)
    identities = {(change_id, author) for change_id, author, _ in applied}
    expected = effective_repository_schema(identities if mode == "baseline" else None)
    connection = get_connection()
    try:
        differences = schema_differences(expected, actual_schema(connection))
    finally:
        connection.close()
    if differences:
        raise RuntimeError("MSSQL_SCHEMA_DRIFT_DETECTED:\n" + "\n".join(differences))
    print(f"MSSQL schema {mode} validation passed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("baseline", "current"), required=True)
    try:
        validate(parser.parse_args().mode)
    except Exception as exc:
        print(exc, file=sys.stderr)
        raise SystemExit(1)
