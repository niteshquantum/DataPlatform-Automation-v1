#!/usr/bin/env python

import json
import sys
from pathlib import Path
import csv
import re
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.python.common.mssql_datatype_validation import validate_mssql_datatype


def detect_datatype(values):

    values = [str(v).strip() for v in values if str(v).strip()]

    if not values:
        return "TEXT"

    # INTEGER
    if all(re.fullmatch(r"-?\d+", v) for v in values):
        return "INTEGER"

    # NUMERIC
    if all(re.fullmatch(r"-?\d+(\.\d+)?", v) for v in values):
        return "NUMERIC"

    # DATE
    try:
        for v in values:
            datetime.strptime(v, "%Y-%m-%d")
        return "DATE"
    except Exception:
        pass

    # TIMESTAMP
    try:
        for v in values:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        return "TIMESTAMP"
    except Exception:
        pass

    return "TEXT"


_MSSQL_TYPE_MAP = {
    "TEXT": "VARCHAR(MAX)",
    "INTEGER": "INT",
    "NUMERIC": "DECIMAL(18,0)",
    "TIMESTAMP": "DATETIME2(7)",
    "DATE": "DATE",
    "BOOLEAN": "BIT",
}


def _mssql_type(value):
    value = str(value or "").strip()
    if not value:
        return ""
    return _MSSQL_TYPE_MAP.get(value.upper(), normalize_mssql_datatype(value))


def resolve_registry_datatype(existing_column, detected):
    """Preserve explicit user choices while still normalizing detected generic defaults."""
    if not isinstance(existing_column, dict):
        return _mssql_type(detected)

    for key in ("final_type", "selected_type", "detected_type"):
        value = existing_column.get(key)
        if not isinstance(value, str) or not value.strip():
            continue

        candidate = value.strip()
        normalized = candidate.upper()

        if normalized in _MSSQL_TYPE_MAP and key == "detected_type":
            return _MSSQL_TYPE_MAP[normalized]

        try:
            validate_mssql_datatype(candidate)
            return candidate
        except ValueError:
            if key in {"selected_type", "final_type"}:
                raise
            if normalized in _MSSQL_TYPE_MAP:
                return _MSSQL_TYPE_MAP[normalized]
            continue

    return _mssql_type(detected)


def main():

    project_root = Path(__file__).parent.parent

    db_type = (
        sys.argv[1].lower()
        if len(sys.argv) > 1
        else "mysql"
    )

    schema_path = (
        project_root
        / "metadata"
        / db_type
        / "schema_registry.json"
    )

    datatype_path = (
        project_root
        / "metadata"
        / db_type
        / "datatype_registry.json"
    )

    existing_registry = {}
    if datatype_path.exists():
        try:
            with open(datatype_path, "r", encoding="utf-8") as f:
                existing_registry = json.load(f)
        except Exception:
            existing_registry = {}

    if not schema_path.exists():
        print("schema_registry.json not found")
        return

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    datatype_registry = {}

    incoming_dir = project_root / "incoming" / db_type

    for table, columns in schema.items():

        datatype_registry[table] = {}

        sample_data = {
            col: []
            for col in columns
        }

        csv_file = incoming_dir / f"{table}.csv"

        if csv_file.exists():

            encodings = [
                "utf-8-sig",
                "utf-8",
                "cp1252",
                "latin-1"
            ]

            file_loaded = False

            for encoding in encodings:

                try:

                    print(
                        f"Reading {csv_file.name} using {encoding}"
                    )

                    with open(
                        csv_file,
                        "r",
                        encoding=encoding,
                        newline=""
                    ) as f:

                        reader = csv.DictReader(f)

                        for row in reader:

                            for col in columns:

                                sample_data[col].append(
                                    row.get(col, "")
                                )

                    print(
                        f"Successfully loaded using {encoding}"
                    )

                    file_loaded = True

                    break

                except UnicodeDecodeError:

                    print(
                        f"Failed with {encoding}"
                    )

                    sample_data = {
                        col: []
                        for col in columns
                    }

                    continue

            if not file_loaded:

                print(
                    f"WARNING : Unable to read {csv_file.name}"
                )

        for column in columns:

            detected = detect_datatype(
                sample_data.get(column, [])
            )

            if db_type == "mssql":
                detected = _mssql_type(detected)

            existing_column = existing_registry.get(table, {}).get(column, {})
            selected_type = resolve_registry_datatype(existing_column, detected)
            final_type = selected_type

            if db_type == "mssql":
                selected_type = _mssql_type(selected_type)
                final_type = _mssql_type(final_type)

            datatype_registry[table][column] = {

                "detected_type": detected,

                "selected_type": selected_type,

                "final_type": final_type,

                "sample_value":
                    sample_data.get(column, [""])[0]
                    if sample_data.get(column)
                    else ""
            }

    datatype_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        datatype_path,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            datatype_registry,
            f,
            indent=4
        )


    print(
        f"Datatype Registry Generated : {datatype_path}"
    )


if __name__ == "__main__":
    main()
