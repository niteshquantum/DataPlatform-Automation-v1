"""
Data Profiling Framework - Main Entry Point

Scans database-specific incoming folders, profiles supported
CSV and JSON datasets, and generates a standard profiling.json
output for downstream reconciliation, assessment, recommendation,
and reporting modules.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd


# ============================================================
# PROJECT ROOT AND IMPORT SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from scripts.profiling.profiling_metrics import (
    calculate_basic_metrics,
    calculate_column_metrics,
    calculate_data_quality_summary,
    detect_profiling_issues,
    summarize_profiling_issues,
)


def load_column_classifications(
    database: str,
) -> Dict[str, Dict[str, str]]:
    """
    Load column classification rules for the selected database.

    Returns a nested dict:
        { "filename.csv": { "column_name": "required|optional|conditional|unknown" } }
    """

    config_path = (
        PROJECT_ROOT
        / "config"
        / "profiling"
        / "column_classifications.json"
    )

    if not config_path.exists():

        return {}

    with config_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        configuration = json.load(file)

    return configuration.get(
        database,
        {},
    )


# ============================================================
# CONSTANTS
# ============================================================

SUPPORTED_DATABASES = (
    "mysql",
    "postgresql",
    "mssql",
    "mongodb",
)

SUPPORTED_FILE_TYPES = (
    ".csv",
    ".json",
)


# ============================================================
# FILE READING
# ============================================================

def read_csv_file(file_path: Path) -> pd.DataFrame:
    """
    Read a CSV file into a pandas DataFrame
    with cross-platform encoding fallback.
    """

    encodings = (
        "utf-8",
        "cp1252",
        "latin-1",
    )

    last_error = None

    for encoding in encodings:
        try:
            return pd.read_csv(
                file_path,
                encoding=encoding,
            )

        except UnicodeDecodeError as error:
            last_error = error

    raise last_error


def read_json_file(file_path: Path) -> pd.DataFrame:
    """
    Read a JSON file into a pandas DataFrame.

    Supports:
        - Standard JSON arrays
        - JSON Lines / NDJSON
        - Single JSON objects
    """

    try:
        return pd.read_json(file_path)

    except ValueError:
        try:
            return pd.read_json(file_path, lines=True)

        except ValueError:
            with file_path.open(
                "r",
                encoding="utf-8",
            ) as file:
                json_data = json.load(file)

            if isinstance(json_data, list):
                return pd.DataFrame(json_data)

            if isinstance(json_data, dict):
                return pd.DataFrame([json_data])

            raise ValueError(
                f"Unsupported JSON structure: {file_path.name}"
            )


def read_dataset(file_path: Path) -> pd.DataFrame:
    """
    Select the correct reader based on file extension.
    """

    extension = file_path.suffix.lower()

    if extension == ".csv":
        return read_csv_file(file_path)

    if extension == ".json":
        return read_json_file(file_path)

    raise ValueError(
        f"Unsupported file type: {extension}"
    )


# ============================================================
# FILE PROFILING
# ============================================================
def profile_file(
    file_path: Path,
    column_rules: Optional[Dict[str, str]] = None,
    primary_keys: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Profile one incoming dataset file.
    """

    dataframe = read_dataset(file_path)

    file_size_bytes = file_path.stat().st_size

    profiling_issues = detect_profiling_issues(
        dataframe,
        column_rules=column_rules,
        primary_keys=primary_keys,
    )

    return {
        "file_name": file_path.name,
        "file_type": file_path.suffix.lower(),
        "file_size_bytes": file_size_bytes,
        "basic_metrics": calculate_basic_metrics(
            dataframe
        ),
        "column_metrics": calculate_column_metrics(
            dataframe
        ),
        "data_quality_summary": (
            calculate_data_quality_summary(
                dataframe
            )
        ),
        "profiling_issue_summary": (
            summarize_profiling_issues(
                profiling_issues
            )
        ),
        "profiling_issues": profiling_issues,
    }

# ============================================================
# DATABASE FOLDER PROFILING
# ============================================================

def get_supported_files(
    incoming_directory: Path,
) -> List[Path]:
    """
    Return supported dataset files from the incoming directory.
    """

    return sorted(
        file_path
        for file_path in incoming_directory.iterdir()
        if file_path.is_file()
        and file_path.suffix.lower() in SUPPORTED_FILE_TYPES
    )


def profile_database(database: str) -> Dict[str, Any]:
    """
    Profile all supported incoming files for one database.
    """

    incoming_directory = (
        PROJECT_ROOT
        / "incoming"
        / database
    )

    output_directory = (
        PROJECT_ROOT
        / "metadata"
        / "profiling"
        / database
    )

    output_file = output_directory / "profiling.json"

    if not incoming_directory.exists():
        raise FileNotFoundError(
            f"Incoming directory not found: "
            f"{incoming_directory}"
        )

    dataset_files = get_supported_files(incoming_directory)

    if not dataset_files:
        raise FileNotFoundError(
            f"No supported CSV or JSON files found in: "
            f"{incoming_directory}"
        )
    print()
    print("=====================================")
    print("DATA PROFILING STARTED")
    print("=====================================")
    print(f"Database       : {database}")
    print(f"Input Directory: {incoming_directory}")
    print(f"Files Found    : {len(dataset_files)}")
    print()

    column_classifications = (
        load_column_classifications(database)
    )

    profiling_results = []
    failed_files = []

    for file_path in dataset_files:

        print(f"Profiling: {file_path.name}")

        column_rules = (
            column_classifications.get(
                file_path.name,
                {},
            )
        )

        primary_keys = [
            column
            for column, semantic in (
                column_rules.items()
            )
            if semantic == "primary_key"
        ]

        try:

            file_result = profile_file(
                file_path,
                column_rules=column_rules,
                primary_keys=primary_keys,
            )
            file_result["status"] = "SUCCESS"

            profiling_results.append(file_result)

            print("Status   : SUCCESS")
            print()

        except Exception as error:

            failed_files.append(
                {
                    "file_name": file_path.name,
                    "status": "FAILED",
                    "error": str(error),
                }
            )

            print("Status   : FAILED")
            print(f"Error    : {error}")
            print()
        # ========================================================
    # CONSOLIDATED DATABASE-LEVEL PROFILING SUMMARY
    # ========================================================

    total_rows = sum(
        dataset["basic_metrics"]["total_rows"]
        for dataset in profiling_results
    )

    total_columns = sum(
        dataset["basic_metrics"]["total_columns"]
        for dataset in profiling_results
    )

    total_input_size_bytes = sum(
        dataset["file_size_bytes"]
        for dataset in profiling_results
    )

    total_null_cells = sum(
        dataset["data_quality_summary"]["total_null_cells"]
        for dataset in profiling_results
    )

    total_duplicate_rows = sum(
        dataset["basic_metrics"]["duplicate_rows"]
        for dataset in profiling_results
    )

    total_profiling_issues = sum(
        dataset["profiling_issue_summary"]["total_issues"]
        for dataset in profiling_results
    )

    total_high_severity_issues = sum(
        dataset["profiling_issue_summary"]["high_severity_issues"]
        for dataset in profiling_results
    )

    total_medium_severity_issues = sum(
        dataset["profiling_issue_summary"]["medium_severity_issues"]
        for dataset in profiling_results
    )

    total_low_severity_issues = sum(
        dataset["profiling_issue_summary"]["low_severity_issues"]
        for dataset in profiling_results
    )
    
    profiling_metadata = {
        "database": database,
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "input_directory": str(incoming_directory),
        "supported_file_types": list(
            SUPPORTED_FILE_TYPES
        ),
    }

    build_number = os.environ.get("BUILD_NUMBER")
    if build_number:
        profiling_metadata["pipeline_build_number"] = build_number

    profiling_output = {
        "profiling_metadata": profiling_metadata,
            "profiling_summary": {
            "total_files_found": len(dataset_files),
            "successful_files": len(profiling_results),
            "failed_files": len(failed_files),
            "total_rows": total_rows,
            "total_columns": total_columns,
            "total_input_size_bytes": total_input_size_bytes,
            "total_null_cells": total_null_cells,
            "total_duplicate_rows": total_duplicate_rows,
            "total_profiling_issues": total_profiling_issues,
            "high_severity_issues": total_high_severity_issues,
            "medium_severity_issues": total_medium_severity_issues,
            "low_severity_issues": total_low_severity_issues,
        },
        "datasets": profiling_results,
        "failures": failed_files,
    }

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            profiling_output,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("=====================================")
    print("DATA PROFILING COMPLETED")
    print("=====================================")
    print(f"Successful Files : {len(profiling_results)}")
    print(f"Failed Files     : {len(failed_files)}")
    print(f"Output           : {output_file}")
    print()

    return profiling_output


# ============================================================
# COMMAND-LINE ENTRY POINT
# ============================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Profile incoming datasets for the selected database."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        choices=SUPPORTED_DATABASES,
        help="Database whose incoming datasets should be profiled.",
    )

    return parser.parse_args()


def main() -> None:
    """
    Main execution function.
    """

    arguments = parse_arguments()

    try:
        profiling_output = profile_database(
            arguments.database
        )

        if profiling_output[
            "profiling_summary"
        ]["failed_files"] > 0:
            sys.exit(1)

    except Exception as error:

        print()
        print("=====================================")
        print("DATA PROFILING FAILED")
        print("=====================================")
        print(f"Error: {error}")
        print()

        sys.exit(1)


if __name__ == "__main__":
    main()