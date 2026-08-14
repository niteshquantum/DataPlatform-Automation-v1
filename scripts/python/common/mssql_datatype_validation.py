"""Validation for explicit MSSQL datatype selections."""
import re


_LENGTH_TYPES = {"VARCHAR", "NVARCHAR", "CHAR", "NCHAR", "VARBINARY"}
_LENGTH_PATTERN = re.compile(r"^([A-Z]+)\s*\(\s*(MAX|[1-9][0-9]*)\s*\)$")
_DECIMAL_PATTERN = re.compile(r"^(DECIMAL|NUMERIC)\s*\(\s*([1-9][0-9]*)\s*,\s*([0-9]+)\s*\)$")
_MSSQL_TYPE_MAP = {
    "TEXT": "VARCHAR(MAX)",
    "INTEGER": "INTEGER",
    "NUMERIC": "DECIMAL(18,0)",
    "TIMESTAMP": "DATETIME2(7)",
    "DATE": "DATE",
    "BOOLEAN": "BIT",
}


def validate_mssql_datatype(value):
    """Reject ambiguous MSSQL types without changing an explicit value.

    SQL Server defaults a bare VARCHAR to length one.  A source contract must
    state a length (or MAX) rather than relying on that server default.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError("MSSQL datatype must be a non-empty string")
    normalized = value.strip().upper()
    length_match = _LENGTH_PATTERN.fullmatch(normalized)
    if length_match:
        base, length = length_match.groups()
        if base in _LENGTH_TYPES:
            if length == "MAX" and base not in {"VARCHAR", "NVARCHAR", "VARBINARY"}:
                raise ValueError(f"MSSQL datatype {base} requires a numeric length")
            return
    if normalized in _LENGTH_TYPES:
        raise ValueError(f"MSSQL datatype {normalized} requires an explicit length or MAX")

    decimal_match = _DECIMAL_PATTERN.fullmatch(normalized)
    if decimal_match:
        _, precision, scale = decimal_match.groups()
        if int(precision) > 38 or int(scale) > int(precision):
            raise ValueError(f"MSSQL datatype {value} has invalid precision or scale")
        return
    if normalized in {"DECIMAL", "NUMERIC"}:
        raise ValueError(f"MSSQL datatype {normalized} requires explicit precision and scale")

    if normalized in {"INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT", "BIT", "DATE", "DATETIME", "DATETIME2", "DATETIMEOFFSET", "TIME", "FLOAT", "REAL", "CHAR", "NCHAR", "VARCHAR(MAX)", "NVARCHAR(MAX)", "VARBINARY(MAX)", "CHAR(1)", "NCHAR(1)", "VARCHAR(255)", "NVARCHAR(255)", "DECIMAL(12,2)", "DECIMAL(10,2)", "DECIMAL(18,0)", "BIT", "INT", "BIGINT"}:
        return

    if normalized in _MSSQL_TYPE_MAP:
        return

    raise ValueError(f"Unsupported MSSQL datatype: {value}")


def normalize_mssql_datatype(value):
    """Convert generic detected aliases to explicit SQL Server types without overwriting valid user selections."""
    if value is None:
        raise ValueError("MSSQL datatype must be a non-empty string")

    raw = str(value).strip()
    if not raw:
        raise ValueError("MSSQL datatype must be a non-empty string")

    normalized = raw.upper()
    if normalized in {"INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT", "BIT", "DATE", "DATETIME", "DATETIME2", "TIME", "FLOAT", "REAL"}:
        validate_mssql_datatype(normalized)
        return normalized

    if normalized in _MSSQL_TYPE_MAP and normalized not in {"INTEGER"}:
        canonical = _MSSQL_TYPE_MAP[normalized]
        validate_mssql_datatype(canonical)
        return canonical

    validate_mssql_datatype(normalized)
    return normalized
