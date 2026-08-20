#!/usr/bin/env python

"""
Column Mapper

Reusable utilities for table name and column name mapping.
"""

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "column_mapping.json"
)


def load_mapping_config():
    """Load column_mapping.json configuration."""
    if not CONFIG_PATH.exists():
        logger.warning(f"Mapping config not found: {CONFIG_PATH}")
        return {"settings": {"enable_mapping": False}}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_name(name, settings):
    """Normalize a name according to mapping settings."""
    if not isinstance(name, str):
        return name

    result = name

    if settings.get("trim_whitespace", True):
        result = result.strip()

    replace = settings.get("replace", {})
    for old, new in replace.items():
        result = result.replace(old, new)

    if settings.get("convert_to_lowercase", True):
        result = result.lower()

    if settings.get("convert_camelcase", False):
        result = re.sub(r"([A-Z])", r"_\1", result).lower()
        if settings.get("remove_duplicate_underscores", True):
            while "__" in result:
                result = result.replace("__", "_")
        if settings.get("remove_leading_trailing_underscores", True):
            result = result.strip("_")

    if settings.get("remove_duplicate_underscores", True):
        while "__" in result:
            result = result.replace("__", "_")

    if settings.get("remove_leading_trailing_underscores", True):
        result = result.strip("_")

    return result


def map_table_name(source_name, config):
    """
    Map a source table name to a target table name.

    Does NOT depend on map_columns().
    """
    settings = config.get("settings", {})
    table_mapping = config.get("table_mapping", {})

    if not settings.get("enable_mapping", False):
        return source_name.strip().lower().replace(" ", "_")

    if source_name in table_mapping:
        return table_mapping[source_name]

    normalized = normalize_name(source_name, settings)
    if normalized in table_mapping:
        return table_mapping[normalized]

    normalized_lower = normalized.lower()
    for key, value in table_mapping.items():
        if key.lower() == normalized_lower:
            return value
        if key.lower() in normalized_lower:
            return value

    return normalized


def _apply_dictionary_mapping(name, dictionary):
    """Apply dictionary-based word replacements to a column name."""
    name_lower = name.lower()
    for src, tgt in dictionary.items():
        src_lower = src.lower()
        if src_lower == name_lower:
            return tgt
        if src_lower in name_lower:
            return name_lower.replace(src_lower, tgt.lower())
    return name


def map_columns(source_headers, config, source_table_name=None):
    """
    Map source column headers to target column names.

    Returns list of target column names.
    Raises ValueError on mapping collision.
    """
    settings = config.get("settings", {})

    if not settings.get("enable_mapping", False):
        return [h.strip() for h in source_headers if isinstance(h, str)]

    manual = config.get("manual", {})
    dictionary = config.get("dictionary", {})
    ignore_columns = [c.lower() for c in config.get("ignore_columns", [])]
    replace = settings.get("replace", {})

    manual_lower = {k.lower(): v for k, v in manual.items()}

    mapped = []
    seen_targets = {}

    for header in source_headers:
        if not isinstance(header, str):
            continue

        cleaned = header.strip()

        if cleaned.lower() in ignore_columns:
            logger.info(f"Ignoring column: {cleaned}")
            continue

        if cleaned in manual:
            target = manual[cleaned]
        elif cleaned.lower() in manual_lower:
            target = manual_lower[cleaned.lower()]
        else:
            target = cleaned
            target = _apply_dictionary_mapping(target, dictionary)
            for old, new in replace.items():
                target = target.replace(old, new)
            target = normalize_name(target, settings)

        if target in seen_targets:
            seen_targets[target].append(cleaned)
        else:
            seen_targets[target] = [cleaned]

        mapped.append(target)

    for target, sources in seen_targets.items():
        if len(sources) > 1:
            raise ValueError(
                f"Column mapping collision: source columns {sources} "
                f"both map to target column '{target}'"
            )

    return mapped


def get_source_to_target_mapping(source_headers, config, source_table_name=None):
    """
    Return a dict mapping source column names to target column names.

    Ignored columns are omitted from the returned mapping.
    """
    settings = config.get("settings", {})

    if not settings.get("enable_mapping", False):
        return {h: h.strip() for h in source_headers if isinstance(h, str)}

    manual = config.get("manual", {})
    dictionary = config.get("dictionary", {})
    ignore_columns = [c.lower() for c in config.get("ignore_columns", [])]
    replace = settings.get("replace", {})
    manual_lower = {k.lower(): v for k, v in manual.items()}

    mapping = {}
    seen_targets = {}

    for header in source_headers:
        if not isinstance(header, str):
            continue

        original = header
        cleaned = header.strip()

        if cleaned.lower() in ignore_columns:
            continue

        if cleaned in manual:
            target = manual[cleaned]
        elif cleaned.lower() in manual_lower:
            target = manual_lower[cleaned.lower()]
        else:
            target = cleaned
            target = _apply_dictionary_mapping(target, dictionary)
            for old, new in replace.items():
                target = target.replace(old, new)
            target = normalize_name(target, settings)

        if target in seen_targets:
            seen_targets[target].append(cleaned)
        else:
            seen_targets[target] = [cleaned]

        mapping[original] = target

    for target, sources in seen_targets.items():
        if len(sources) > 1:
            raise ValueError(
                f"Column mapping collision: source columns {sources} "
                f"both map to target column '{target}'"
            )

    return mapping


def resolve_table_mapping(source_name, config):
    """
    Resolve the target table name for a given source table name.
    """
    return map_table_name(source_name, config)


def resolve_source_file_stem(target_table_name, config, db_type):
    """
    Resolve the original source CSV file stem for a given target table name.

    Uses metadata/<db_type>/table_source_mapping.json when mapping is enabled.
    Falls back to the target table name when mapping is disabled or when no
    mapping metadata is available.
    """
    settings = config.get("settings", {})

    if not settings.get("enable_mapping", False):
        return target_table_name

    project_root = Path(__file__).resolve().parents[3]

    mapping_path = (
        project_root
        / "metadata"
        / db_type
        / "table_source_mapping.json"
    )

    if not mapping_path.exists():
        return target_table_name

    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    except (json.JSONDecodeError, OSError):

        logger.warning(
            f"Could not read table source mapping: {mapping_path}"
        )

        return target_table_name

    return mapping.get(target_table_name, target_table_name)
