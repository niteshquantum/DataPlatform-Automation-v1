"""Format-independent datatype detection from sampled column values."""

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Sequence


_INTEGER_PATTERN = re.compile(r"^[+-]?\d+$")
_DECIMAL_PATTERN = re.compile(r"^[+-]?(?:\d+\.\d*|\d*\.\d+)$")
_SCIENTIFIC_PATTERN = re.compile(
    r"^[+-]?(?:\d+\.\d*|\d*\.\d+|\d+)[eE][+-]?\d+$"
)
_BOOLEAN_VALUES = {"true", "false"}
_INT_MIN = -(2**31)
_INT_MAX = 2**31 - 1
_BIGINT_MIN = -(2**63)
_BIGINT_MAX = 2**63 - 1


def _detect_value_type(value: object) -> str | None:
    """Return the datatype represented by one non-empty value."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, datetime):
        return "DATETIME"
    if isinstance(value, date):
        return "DATE"
    if isinstance(value, int):
        return "INT" if _INT_MIN <= value <= _INT_MAX else "BIGINT"
    if isinstance(value, Decimal):
        return "DECIMAL"
    if isinstance(value, float):
        return "DOUBLE"
    if not isinstance(value, str):
        return "VARCHAR"

    sample = value.strip()
    if not sample:
        return None
    if sample.lower() in _BOOLEAN_VALUES:
        return "BOOLEAN"
    if _INTEGER_PATTERN.fullmatch(sample):
        try:
            integer = int(sample)
        except ValueError:
            return "VARCHAR"
        if _INT_MIN <= integer <= _INT_MAX:
            return "INT"
        if _BIGINT_MIN <= integer <= _BIGINT_MAX:
            return "BIGINT"
        return "VARCHAR"
    if _DECIMAL_PATTERN.fullmatch(sample):
        return "DECIMAL"
    if _SCIENTIFIC_PATTERN.fullmatch(sample):
        return "DOUBLE"
    if _is_datetime(sample):
        return "DATETIME"
    if _is_date(sample):
        return "DATE"
    return "VARCHAR"


def _is_datetime(value: str) -> bool:
    """Check whether a value is an ISO-style datetime, not just a date."""
    if "T" not in value and " " not in value:
        return False
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
        return True
    except ValueError:
        return False


def _is_date(value: str) -> bool:
    """Check whether a value is an ISO date."""
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def _resolve_detected_types(detected_types: set[str]) -> str:
    """Return the safest common datatype for compatible sampled values."""
    if not detected_types or "VARCHAR" in detected_types:
        return "VARCHAR"
    if detected_types <= {"INT", "BIGINT"}:
        return "BIGINT" if "BIGINT" in detected_types else "INT"
    if detected_types <= {"INT", "BIGINT", "DECIMAL"}:
        return "DECIMAL"
    if detected_types <= {"INT", "BIGINT", "DECIMAL", "FLOAT", "DOUBLE"}:
        return "DOUBLE" if "DOUBLE" in detected_types else "FLOAT"
    if detected_types <= {"DATE", "DATETIME"}:
        return "DATETIME" if "DATETIME" in detected_types else "DATE"
    return next(iter(detected_types)) if len(detected_types) == 1 else "VARCHAR"


def detect_datatype(column_name: str, sample_values: Sequence[object]) -> str:
    """Detect a column datatype using only its sampled values.

    ``column_name`` is accepted for caller context but intentionally does not
    influence detection so every reader can reuse this function unchanged.
    """
    del column_name
    detected_types = {
        detected_type
        for value in sample_values
        if (detected_type := _detect_value_type(value)) is not None
    }
    return _resolve_detected_types(detected_types)
