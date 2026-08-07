"""Reusable column-name mapping utilities."""

import json
import logging
import re
from functools import lru_cache
from pathlib import Path
from types import MappingProxyType
from typing import List, Mapping


logger = logging.getLogger(__name__)


def _mapping_config_path() -> Path:
    """Return the shared column-mapping configuration path."""
    project_root = Path(__file__).resolve().parent.parents[2]
    return project_root / "config" / "column_mapping.json"


def _normalize_column_name(column: str) -> str:
    """Convert a source column name to a standard underscore-separated form."""
    normalized = re.sub(r"[^a-z0-9]+", "_", column.strip().lower())
    return normalized.strip("_")


def _normalized_mappings(mappings: object) -> Mapping[str, str]:
    """Return valid string mappings with normalized keys."""
    if not isinstance(mappings, dict):
        return MappingProxyType({})

    return MappingProxyType(
        {
            _normalize_column_name(key): value
            for key, value in mappings.items()
            if isinstance(key, str) and isinstance(value, str)
        }
    )


@lru_cache(maxsize=1)
def _load_mappings() -> tuple[Mapping[str, str], Mapping[str, str]]:
    """Load manual and dictionary mappings without interrupting processing."""
    config_path = _mapping_config_path()

    if not config_path.exists():
        logger.info("Column mapping configuration not found: %s", config_path)
        return MappingProxyType({}), MappingProxyType({})

    try:
        with config_path.open("r", encoding="utf-8") as config_file:
            config = json.load(config_file)
    except (OSError, json.JSONDecodeError) as error:
        logger.error("Error reading column mapping configuration %s: %s", config_path, error)
        return MappingProxyType({}), MappingProxyType({})

    manual = config.get("manual", {})
    dictionary = config.get("dictionary", {})

    return _normalized_mappings(manual), _normalized_mappings(dictionary)


def map_columns(columns: List[str]) -> List[str]:
    """Map columns using manual mappings, dictionary mappings, then normalization."""
    manual_mappings, dictionary_mappings = _load_mappings()
    mapped_columns = []
    source_columns_by_destination = {}

    for column in columns:
        normalized_column = _normalize_column_name(column)
        mapped_column = manual_mappings.get(normalized_column)

        if mapped_column is None:
            mapped_column = dictionary_mappings.get(normalized_column, normalized_column)

        if not mapped_column:
            mapped_column = column

        logger.info("Original column: %s | Mapped column: %s", column, mapped_column)
        if mapped_column in source_columns_by_destination:
            logger.warning(
                "Multiple source columns mapped to destination column '%s'",
                mapped_column,
            )
        else:
            source_columns_by_destination[mapped_column] = column
        mapped_columns.append(mapped_column)

    return mapped_columns
def map_table_name(table_name):
    return map_columns([table_name])[0]
