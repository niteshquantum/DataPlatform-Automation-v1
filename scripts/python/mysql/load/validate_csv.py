import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]

schema_file = ROOT / "metadata" / "mysql" / "schema_registry.json"
incoming_dir = ROOT / "incoming" / "mysql"

try:
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_registry = json.load(f)

    print()
    print("=" * 50)
    print("CSV VALIDATION")
    print("=" * 50)

    for table_name, required_columns in schema_registry.items():

        csv_file = incoming_dir / f"{table_name}.csv"

        if not csv_file.exists():
            archive_file = ROOT / "archive" / "mysql" / f"{table_name}.csv"
            failed_file = ROOT / "failed" / "mysql" / f"{table_name}.csv"

            if archive_file.exists() or failed_file.exists():
                print(f"[SKIPPED] {csv_file.name} already processed")
                continue

            raise Exception(f"Required file missing: {csv_file.name}")

        last_error = None
        for encoding in ["utf-8-sig", "cp1252", "latin-1"]:
            try:
                df = pd.read_csv(csv_file, encoding=encoding)
                break
            except UnicodeDecodeError as exc:
                last_error = exc
        else:
            raise last_error

        if df.empty:
            raise Exception(
                f"CSV file is empty: {csv_file.name}"
            )

        missing_columns = [
            column
            for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise Exception(
                f"{csv_file.name} missing columns: "
                f"{', '.join(missing_columns)}"
            )

        print(
            f"[OK] {csv_file.name} "
            f"({len(df)} rows)"
        )

    print("=" * 50)
    print("CSV VALIDATION SUCCESS")
    print("=" * 50)

except Exception as e:

    print()
    print("=" * 50)
    print("CSV VALIDATION FAILED")
    print("=" * 50)
    print(e)
    print("=" * 50)

    raise SystemExit(1)
