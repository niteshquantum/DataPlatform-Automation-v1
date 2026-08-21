#!/usr/bin/env python

"""
Generic Datatype Resolver

Converts Schema Editor logical types into database-specific physical
SQL types. Reads mappings from config/common/datatype_rules.json.

No dependency on naming, schema detection, Liquibase, or data loading.
"""

import json
from pathlib import Path


class UnsupportedDatabaseError(Exception):
    pass


class UnsupportedTypeError(Exception):
    pass


class MissingConfigError(Exception):
    pass


_ROOT = Path(__file__).resolve().parents[3]
_CONFIG_PATH = _ROOT / "config" / "common" / "datatype_rules.json"


def _load_config():
    if not _CONFIG_PATH.exists():
        raise MissingConfigError(
            f"datatype_rules.json not found: {_CONFIG_PATH}"
        )
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_db(db_type: str) -> str:
    if not isinstance(db_type, str):
        raise TypeError("db_type must be a string")
    normalized = db_type.strip().upper()
    mapping = {
        "MYSQL": "MYSQL",
        "POSTGRESQL": "POSTGRESQL",
        "MSSQL": "MSSQL",
    }
    if normalized not in mapping:
        raise UnsupportedDatabaseError(
            f"Unsupported database type: {db_type!r}. "
            f"Supported: mysql, postgresql, mssql."
        )
    return mapping[normalized]


def _normalize_logical_type(logical_type: str) -> str:
    if not isinstance(logical_type, str):
        raise TypeError("logical_type must be a string")
    normalized = logical_type.strip().upper()
    if not normalized:
        raise UnsupportedTypeError("Logical type must not be empty.")
    return normalized


def load_datatype_registry(db_type: str) -> dict:
    config = _load_config()
    db_key = _normalize_db(db_type)
    registry = {}
    types_cfg = config.get("types", {}).get(db_key, {})
    for logical, physical in types_cfg.items():
        registry[_normalize_logical_type(logical)] = physical
    return registry


def map_to_physical_type(logical_type: str, db_type: str) -> str:
    if not isinstance(logical_type, str) or not logical_type.strip():
        raise UnsupportedTypeError("logical_type must be a non-empty string.")
    registry = load_datatype_registry(db_type)
    key = _normalize_logical_type(logical_type)
    if key not in registry:
        raise UnsupportedTypeError(
            f"Unsupported logical type: {logical_type!r} "
            f"for database {db_type!r}. "
            f"Supported logical types: {sorted(registry.keys())}."
        )
    return registry[key]


def resolve_logical_type(
    table_name: str,
    column_name: str,
    registry: dict,
) -> str:
    if not isinstance(table_name, str):
        raise TypeError("table_name must be a string")
    if not isinstance(column_name, str):
        raise TypeError("column_name must be a string")
    if not isinstance(registry, dict):
        raise TypeError("registry must be a dict")

    table = registry.get(table_name, {})
    if not isinstance(table, dict):
        raise ValueError(
            f"Table {table_name!r} not found in datatype registry."
        )

    column = table.get(column_name)
    if column is None:
        raise ValueError(
            f"Column {column_name!r} not found in table {table_name!r}."
        )

    selected = column.get("selected_type")
    detected = column.get("detected_type")

    if (
        isinstance(selected, str)
        and selected.strip()
        and selected.strip().lower() != "null"
    ):
        return selected.strip()

    if (
        isinstance(detected, str)
        and detected.strip()
        and detected.strip().lower() != "null"
    ):
        return detected.strip()

    config = _load_config()
    return config.get("settings", {}).get("default_logical_type", "TEXT")


def resolve_column_type(
    table_name: str,
    column_name: str,
    db_type: str,
    registry: dict = None,
) -> str:
    if registry is None:
        registry = load_datatype_registry(db_type)
    logical = resolve_logical_type(table_name, column_name, registry)
    return map_to_physical_type(logical, db_type)


def get_column_type(
    registry: dict,
    table_name: str,
    column_name: str,
    db_type: str,
) -> str:
    return resolve_column_type(table_name, column_name, db_type, registry)


__all__ = [
    "load_datatype_registry",
    "map_to_physical_type",
    "resolve_logical_type",
    "resolve_column_type",
    "get_column_type",
    "UnsupportedDatabaseError",
    "UnsupportedTypeError",
    "MissingConfigError",
]
