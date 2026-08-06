#!/usr/bin/env python

import json
import sys
from pathlib import Path
import csv
import re
from datetime import datetime

def detect_datatype(values):
    
    values = [str(v).strip() for v in values if str(v).strip()]

    if not values:
        return "TEXT"

    # INTEGER
    if all(re.fullmatch(r"-?\d+", v) for v in values):
        return "INTEGER"

    # NUMERIC / DECIMAL
    if all(re.fullmatch(r"-?\d+(\.\d+)?", v) for v in values):
        return "NUMERIC"

    # DATE
    try:
        for v in values:
            datetime.strptime(v, "%Y-%m-%d")
        return "DATE"
    except:
        pass

    # TIMESTAMP
    try:
        for v in values:
            datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
        return "TIMESTAMP"
    except:
        pass

    return "TEXT"
def main():

    project_root = Path(__file__).parent.parent

    db_type = sys.argv[1].lower() if len(sys.argv) > 1 else "mysql"

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

    if not schema_path.exists():
        print("schema_registry.json not found")
        return

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    datatype_registry = {}

    incoming_dir = project_root / "incoming" / db_type

    for table, columns in schema.items():

        datatype_registry[table] = {}

        csv_file = incoming_dir / f"{table}.csv"

        sample_data = {}

        if csv_file.exists():
            sample_data = {}

            try:

                f = open(
                    csv_file,
                    "r",
                    encoding="utf-8-sig"
                )

            except UnicodeDecodeError:

                f = open(
                    csv_file,
                    "r",
                    encoding="latin-1"
                )

            with f:

                reader = csv.DictReader(f)

                for col in columns:
                    sample_data[col] = []

                for row in reader:

                    for col in columns:

                        sample_data[col].append(
                            row.get(col, "")
                        )
        for column in columns:

            detected = detect_datatype(sample_data.get(column, []))

            datatype_registry[table][column] = {
            "detected_type": detected,
            "selected_type": detected,
            "sample_value": sample_data.get(column, [""])[0] if sample_data.get(column) else ""
            }

    datatype_path.parent.mkdir(parents=True, exist_ok=True)

    with open(datatype_path, "w", encoding="utf-8") as f:
        json.dump(datatype_registry, f, indent=4)

    print(f"Datatype Registry Generated : {datatype_path}")


if __name__ == "__main__":
    main()