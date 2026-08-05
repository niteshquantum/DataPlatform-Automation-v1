"""Reusable runtime datatype override utilities."""

import json
import logging
import sys
from functools import lru_cache
from pathlib import Path
from typing import Callable


logger = logging.getLogger(__name__)
DEFAULT_SUPPORTED_DATATYPES = (
    "INT",
    "BIGINT",
    "FLOAT",
    "DOUBLE",
    "DECIMAL",
    "BOOLEAN",
    "DATE",
    "DATETIME",
    "VARCHAR",
)


def _config_path() -> Path:
    """Return the persistent datatype override configuration path."""
    project_root = Path(__file__).parent.parent.parent.parent
    return project_root / "config" / "datatype_override.json"


@lru_cache(maxsize=1)
def _load_supported_datatypes() -> tuple[str, ...]:
    """Load supported datatypes once, falling back to the current list."""
    rules_path = _config_path().with_name("datatype_rules.json")

    try:
        with rules_path.open("r", encoding="utf-8") as rules_file:
            rules = json.load(rules_file)
    except (OSError, json.JSONDecodeError) as error:
        logger.error("Error reading datatype rules %s: %s", rules_path, error)
        return DEFAULT_SUPPORTED_DATATYPES

    supported_datatypes = (
        rules.get("supported_datatypes") if isinstance(rules, dict) else None
    )
    if (
        not isinstance(supported_datatypes, list)
        or not supported_datatypes
        or not all(
            isinstance(datatype, str) and datatype.strip()
            for datatype in supported_datatypes
        )
    ):
        return DEFAULT_SUPPORTED_DATATYPES

    return tuple(supported_datatypes)


def _override_key(table_name: str, column_name: str) -> str:
    """Build the file-type-independent override key for a column."""
    return f"{table_name}.{column_name}"


def _load_overrides() -> dict[str, str]:
    """Load saved overrides, creating an empty configuration when needed."""
    config_path = _config_path()

    try:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        if not config_path.exists():
            with config_path.open("w", encoding="utf-8") as config_file:
                json.dump({}, config_file, indent=2)

        with config_path.open("r", encoding="utf-8") as config_file:
            overrides = json.load(config_file)
    except (OSError, json.JSONDecodeError) as error:
        logger.error("Error reading datatype overrides %s: %s", config_path, error)
        return {}

    if not isinstance(overrides, dict):
        logger.error("Invalid datatype override configuration: %s", config_path)
        return {}

    return {
        key: value
        for key, value in overrides.items()
        if isinstance(key, str) and isinstance(value, str) and value.strip()
    }


def _save_override(table_name: str, column_name: str, datatype: str) -> None:
    """Persist a selected datatype so later runs reuse it."""
    config_path = _config_path()
    overrides = _load_overrides()
    overrides[_override_key(table_name, column_name)] = datatype

    try:
        with config_path.open("w", encoding="utf-8") as config_file:
            json.dump(overrides, config_file, indent=2)
    except OSError as error:
        logger.error("Error saving datatype override %s: %s", config_path, error)


def prompt_datatype_override(
    table_name: str, column_name: str, detected_type: str
) -> str | None:
    """Prompt for a valid datatype selection when standard input is interactive."""
    if not sys.stdin.isatty():
        logger.info(
            "No interactive input available for %s; using detected datatype %s",
            _override_key(table_name, column_name),
            detected_type,
        )
        return None

    supported_datatypes = _load_supported_datatypes()
    options = "\n".join(
        f"{index}. {datatype}"
        for index, datatype in enumerate(supported_datatypes, start=1)
    )
    prompt = (
        f"\nColumn : {column_name}\n"
        f"Detected datatype : {detected_type}\n"
        f"Available datatypes\n{options}\n"
        "Press ENTER to keep detected datatype.\n"
        "Choice : "
    )

    try:
        choice = input(prompt).strip()
    except (EOFError, OSError):
        logger.info("No datatype override selected for %s", _override_key(table_name, column_name))
        return None

    if not choice:
        return detected_type
    if choice.isdigit() and 1 <= int(choice) <= len(supported_datatypes):
        return supported_datatypes[int(choice) - 1]

    logger.warning("Invalid datatype override choice for %s", _override_key(table_name, column_name))
    return None


def resolve_datatype(
    table_name: str,
    column_name: str,
    detected_type: str,
    callback: Callable[[str, str, str], str | None] | None = None,
) -> str:
    """Return a saved or callback-selected datatype, falling back to detection."""
    override_key = _override_key(table_name, column_name)
    saved_override = _load_overrides().get(override_key)

    if saved_override:
        logger.info("Using saved datatype override for %s: %s", override_key, saved_override)
        return saved_override

    if callback is None:
        return detected_type

    try:
        selected_override = callback(table_name, column_name, detected_type)
    except Exception as error:
        logger.error("Error selecting datatype override for %s: %s", override_key, error)
        return detected_type

    if selected_override:
        _save_override(table_name, column_name, selected_override)
        return selected_override

    return detected_type
