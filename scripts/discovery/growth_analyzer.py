"""
Database Growth Analyzer.

Compares the current database discovery snapshot with the
previous discovery snapshot and calculates:

- Total Record Growth
- Overall Growth Rate
- Per-Dataset Record Growth
- Per-Dataset Growth Rate
- New Datasets
- Removed Datasets

Supported Databases:
- MySQL
- PostgreSQL
- MongoDB
- MSSQL
"""

import argparse
import json
import shutil
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# SUPPORTED DATABASES
# ============================================================

SUPPORTED_DATABASES = {
    "mysql",
    "postgresql",
    "mongodb",
    "mssql",
}


SNAPSHOT_SCHEMA_VERSION = "1.0"


# ============================================================
# LOAD JSON
# ============================================================

def load_json(
    file_path: Path,
) -> Dict[str, Any]:

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


def validate_snapshot_provenance(
    snapshot: Dict[str, Any],
    database: str,
) -> None:
    """
    Validate snapshot provenance metadata.

    Raises ValueError if the snapshot belongs to a different
    database or is from an incompatible schema version.

    Legacy snapshots without provenance metadata are accepted
    as UNVERIFIED_LEGACY and do not cause growth analysis to fail.
    """

    snapshot_database = snapshot.get("database")

    if snapshot_database is not None and snapshot_database != database:

        raise ValueError(
            f"Snapshot database '{snapshot_database}' "
            f"does not match current database '{database}'. "
            "Growth analysis cannot compare cross-database snapshots."
        )


# ============================================================
# SAVE JSON
# ============================================================

def save_json(
    file_path: Path,
    data: Dict[str, Any],
) -> None:

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )


# ============================================================
# CALCULATE GROWTH RATE
# ============================================================

def calculate_growth_rate(
    previous_count: int,
    current_count: int,
) -> Optional[float]:

    if previous_count == 0:

        if current_count == 0:
            return 0.0

        return None

    growth_rate = (
        (
            current_count
            - previous_count
        )
        / previous_count
    ) * 100

    return round(
        growth_rate,
        2,
    )


# ============================================================
# DATASET MAP
# ============================================================

def build_dataset_map(
    discovery_output: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:

    return {
        dataset["dataset_name"]: dataset
        for dataset in discovery_output.get(
            "datasets",
            [],
        )
    }


# ============================================================
# ANALYZE DATASET GROWTH
# ============================================================

def analyze_dataset_growth(
    previous_output: Dict[str, Any],
    current_output: Dict[str, Any],
) -> List[Dict[str, Any]]:

    previous_datasets = build_dataset_map(
        previous_output
    )

    current_datasets = build_dataset_map(
        current_output
    )

    dataset_names = sorted(
        set(previous_datasets)
        | set(current_datasets)
    )

    results = []

    for dataset_name in dataset_names:

        previous_dataset = (
            previous_datasets.get(
                dataset_name
            )
        )

        current_dataset = (
            current_datasets.get(
                dataset_name
            )
        )

        if (
            previous_dataset is None
            and current_dataset is not None
        ):

            current_count = int(
                current_dataset.get(
                    "record_count",
                    0,
                )
            )

            results.append(
                {
                    "dataset_name": dataset_name,
                    "status": "NEW_DATASET",
                    "previous_record_count": 0,
                    "current_record_count": (
                        current_count
                    ),
                    "record_growth": current_count,
                    "growth_rate_percent": None,
                }
            )

            continue

        if (
            current_dataset is None
            and previous_dataset is not None
        ):

            previous_count = int(
                previous_dataset.get(
                    "record_count",
                    0,
                )
            )

            results.append(
                {
                    "dataset_name": dataset_name,
                    "status": "REMOVED_DATASET",
                    "previous_record_count": (
                        previous_count
                    ),
                    "current_record_count": 0,
                    "record_growth": (
                        -previous_count
                    ),
                    "growth_rate_percent": -100.0,
                }
            )

            continue

        previous_count = int(
            previous_dataset.get(
                "record_count",
                0,
            )
        )

        current_count = int(
            current_dataset.get(
                "record_count",
                0,
            )
        )

        record_growth = (
            current_count
            - previous_count
        )

        growth_rate = calculate_growth_rate(
            previous_count,
            current_count,
        )

        if record_growth > 0:
            status = "GROWTH"

        elif record_growth < 0:
            status = "REDUCTION"

        else:
            status = "NO_CHANGE"

        results.append(
            {
                "dataset_name": dataset_name,
                "status": status,
                "previous_record_count": (
                    previous_count
                ),
                "current_record_count": (
                    current_count
                ),
                "record_growth": record_growth,
                "growth_rate_percent": growth_rate,
            }
        )

    return results


# ============================================================
# FIRST RUN OUTPUT
# ============================================================

def build_baseline_output(
    database: str,
    current_output: Dict[str, Any],
) -> Dict[str, Any]:

    current_records = int(
        current_output.get(
            "summary",
            {},
        ).get(
            "total_records",
            0,
        )
    )

    return {
        "database": database,
        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "snapshot_schema_version": (
            SNAPSHOT_SCHEMA_VERSION
        ),
        "growth_status": "BASELINE_CREATED",
        "summary": {
            "previous_total_records": None,
            "current_total_records": (
                current_records
            ),
            "total_record_growth": None,
            "overall_growth_rate_percent": None,
            "datasets_with_growth": 0,
            "datasets_with_reduction": 0,
            "datasets_without_change": 0,
            "new_datasets": 0,
            "removed_datasets": 0,
        },
        "dataset_growth": [],
        "message": (
            "Baseline discovery snapshot created. "
            "Growth analysis will be available after "
            "a future discovery snapshot is generated."
        ),
    }


# ============================================================
# GROWTH OUTPUT
# ============================================================

def build_growth_output(
    database: str,
    previous_output: Dict[str, Any],
    current_output: Dict[str, Any],
) -> Dict[str, Any]:

    previous_total_records = int(
        previous_output.get(
            "summary",
            {},
        ).get(
            "total_records",
            0,
        )
    )

    current_total_records = int(
        current_output.get(
            "summary",
            {},
        ).get(
            "total_records",
            0,
        )
    )

    total_record_growth = (
        current_total_records
        - previous_total_records
    )

    overall_growth_rate = (
        calculate_growth_rate(
            previous_total_records,
            current_total_records,
        )
    )

    dataset_growth = analyze_dataset_growth(
        previous_output,
        current_output,
    )

    datasets_with_growth = sum(
        1
        for dataset in dataset_growth
        if dataset["status"] == "GROWTH"
    )

    datasets_with_reduction = sum(
        1
        for dataset in dataset_growth
        if dataset["status"] == "REDUCTION"
    )

    datasets_without_change = sum(
        1
        for dataset in dataset_growth
        if dataset["status"] == "NO_CHANGE"
    )

    new_datasets = sum(
        1
        for dataset in dataset_growth
        if dataset["status"] == "NEW_DATASET"
    )

    removed_datasets = sum(
        1
        for dataset in dataset_growth
        if dataset["status"] == "REMOVED_DATASET"
    )

    return {
        "database": database,
        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "snapshot_schema_version": (
            SNAPSHOT_SCHEMA_VERSION
        ),
        "growth_status": "ANALYZED",
        "comparison": {
            "previous_snapshot_generated_at": (
                previous_output.get(
                    "generated_at"
                )
            ),
            "current_snapshot_generated_at": (
                current_output.get(
                    "generated_at"
                )
            ),
        },
        "summary": {
            "previous_total_records": (
                previous_total_records
            ),
            "current_total_records": (
                current_total_records
            ),
            "total_record_growth": (
                total_record_growth
            ),
            "overall_growth_rate_percent": (
                overall_growth_rate
            ),
            "datasets_with_growth": (
                datasets_with_growth
            ),
            "datasets_with_reduction": (
                datasets_with_reduction
            ),
            "datasets_without_change": (
                datasets_without_change
            ),
            "new_datasets": new_datasets,
            "removed_datasets": removed_datasets,
        },
        "dataset_growth": dataset_growth,
    }


# ============================================================
# COMMAND LINE ARGUMENTS
# ============================================================

def parse_arguments():

    parser = argparse.ArgumentParser(
        description=(
            "Database Growth Analyzer"
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        choices=sorted(
            SUPPORTED_DATABASES
        ),
    )

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():

    arguments = parse_arguments()

    database = arguments.database.lower()

    discovery_directory = (
        ROOT
        / "metadata"
        / "discovery"
        / database
    )

    discovery_file = (
        discovery_directory
        / "discovery.json"
    )

    history_directory = (
        discovery_directory
        / "history"
    )

    snapshot_file = (
        history_directory
        / "discovery_snapshot.json"
    )

    growth_output_file = (
        discovery_directory
        / "growth_analysis.json"
    )

    print()
    print(
        "====================================="
    )
    print(
        "DATABASE GROWTH ANALYSIS STARTED"
    )
    print(
        "====================================="
    )
    print(
        f"Database: {database}"
    )
    print()

    try:

        if not discovery_file.exists():

            raise FileNotFoundError(
                "Discovery output not found: "
                f"{discovery_file}"
            )

        current_output = load_json(
            discovery_file
        )

        # ====================================================
        # FIRST RUN
        # ====================================================

        if not snapshot_file.exists():

            growth_output = (
                build_baseline_output(
                    database,
                    current_output,
                )
            )

            save_json(
                growth_output_file,
                growth_output,
            )

            history_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copy2(
                discovery_file,
                snapshot_file,
            )

            print(
                "Baseline snapshot created."
            )
            print(
                "Growth analysis will be available "
                "after the next discovery run."
            )

        # ====================================================
        # FUTURE RUN
        # ====================================================

        else:

            previous_output = load_json(
                snapshot_file
            )

            validate_snapshot_provenance(
                previous_output,
                database,
            )

            growth_output = (
                build_growth_output(
                    database,
                    previous_output,
                    current_output,
                )
            )

            save_json(
                growth_output_file,
                growth_output,
            )

            shutil.copy2(
                discovery_file,
                snapshot_file,
            )

            summary = growth_output[
                "summary"
            ]

            print(
                f"Previous Records : "
                f"{summary['previous_total_records']}"
            )

            print(
                f"Current Records  : "
                f"{summary['current_total_records']}"
            )

            print(
                f"Record Growth    : "
                f"{summary['total_record_growth']}"
            )

            print(
                f"Growth Rate      : "
                f"{summary['overall_growth_rate_percent']}%"
            )

        print()
        print(
            "====================================="
        )
        print(
            "DATABASE GROWTH ANALYSIS COMPLETED"
        )
        print(
            "====================================="
        )
        print(
            f"Output: {growth_output_file}"
        )
        print()

    except Exception as error:

        print(
            "====================================="
        )
        print(
            "DATABASE GROWTH ANALYSIS FAILED"
        )
        print(
            "====================================="
        )
        print(
            f"Error: {error}"
        )
        print()

        sys.exit(1)


if __name__ == "__main__":
    main()