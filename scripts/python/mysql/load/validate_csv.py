import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]

schema_file = ROOT / "metadata" / "mysql" / "schema_registry.json"
incoming_dir = ROOT / "incoming" / "mysql"
archive_dir = ROOT / "archive" / "mysql"
failed_dir = ROOT / "failed" / "mysql"

from scripts.python.common.column_mapper import (
    load_mapping_config,
    resolve_source_file_stem,
    get_source_to_target_mapping,
)

try:
    with open(schema_file, "r", encoding="utf-8") as f:
        schema_registry = json.load(f)

    print()
    print("=" * 50)
    print("CSV VALIDATION")
    print("=" * 50)

    mapping_config = load_mapping_config()

    for table_name, required_columns in schema_registry.items():

        source_stem = resolve_source_file_stem(table_name, mapping_config, "mysql")
        csv_file = incoming_dir / f"{source_stem}.csv"

        if not csv_file.exists():
            archive_file = archive_dir / f"{source_stem}.csv"
            failed_file = failed_dir / f"{source_stem}.csv"

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

        source_headers = list(df.columns)
        source_to_target = get_source_to_target_mapping(source_headers, mapping_config)
        target_to_source = {v: k for k, v in source_to_target.items()}

        missing_columns = []
        for target_col in required_columns:
            source_col = target_to_source.get(target_col)
            if source_col is None or source_col not in source_headers:
                missing_columns.append(target_col)

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
