"""
Common profiling metric utilities.

This module calculates reusable dataset-level, column-level,
and data-quality metrics for incoming datasets.

The generated metrics are database-independent and support
CSV files as well as MongoDB-style nested JSON datasets.

The profiling output is designed to support future
reconciliation, assessment, recommendation, technical reporting,
and executive reporting modules.
"""

import json
from typing import Any, Dict, List, Optional

import pandas as pd


# ============================================================
# HASHABLE DATAFRAME CONVERSION
# ============================================================

def make_dataframe_hashable(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Create a profiling-safe DataFrame copy.

    MongoDB JSON datasets may contain nested dictionaries
    and arrays. Pandas duplicated() and nunique() operations
    cannot directly process unhashable list and dictionary values.

    Nested values are converted into stable JSON strings only
    for metric calculation.

    The original source DataFrame is not modified.
    """

    safe_dataframe = dataframe.copy()

    for column_name in safe_dataframe.columns:

        safe_dataframe[column_name] = (
            safe_dataframe[column_name].apply(
                lambda value: json.dumps(
                    value,
                    sort_keys=True,
                    ensure_ascii=False,
                )
                if isinstance(value, (list, dict))
                else value
            )
        )

    return safe_dataframe


# ============================================================
# BASIC DATASET METRICS
# ============================================================

def calculate_basic_metrics(
    dataframe: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Calculate basic dataset-level profiling metrics.
    """

    safe_dataframe = make_dataframe_hashable(
        dataframe
    )

    total_rows = len(dataframe)

    total_columns = len(
        dataframe.columns
    )

    duplicate_rows = int(
        safe_dataframe.duplicated().sum()
    )

    duplicate_percentage = (
        round(
            (duplicate_rows / total_rows) * 100,
            2,
        )
        if total_rows > 0
        else 0.0
    )

    memory_usage_bytes = int(
        dataframe.memory_usage(
            index=True,
            deep=True,
        ).sum()
    )

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "duplicate_rows": duplicate_rows,
        "duplicate_percentage": duplicate_percentage,
        "memory_usage_bytes": memory_usage_bytes,
    }


# ============================================================
# COLUMN METRICS
# ============================================================

def calculate_column_metrics(
    dataframe: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Calculate detailed column-level profiling metrics.

    Nested MongoDB arrays and dictionaries are converted into
    stable JSON representations before uniqueness calculations.
    """

    safe_dataframe = make_dataframe_hashable(
        dataframe
    )

    column_metrics = {}

    total_rows = len(dataframe)

    for column_name in dataframe.columns:

        original_column = dataframe[
            column_name
        ]

        safe_column = safe_dataframe[
            column_name
        ]

        null_count = int(
            original_column.isnull().sum()
        )

        non_null_count = int(
            original_column.notnull().sum()
        )

        unique_count = int(
            safe_column.nunique(
                dropna=True
            )
        )

        null_percentage = (
            round(
                (null_count / total_rows) * 100,
                2,
            )
            if total_rows > 0
            else 0.0
        )

        uniqueness_percentage = (
            round(
                (
                    unique_count
                    / non_null_count
                )
                * 100,
                2,
            )
            if non_null_count > 0
            else 0.0
        )

        column_metrics[
            str(column_name)
        ] = {
            "detected_data_type": str(
                original_column.dtype
            ),
            "null_count": null_count,
            "null_percentage": (
                null_percentage
            ),
            "non_null_count": (
                non_null_count
            ),
            "unique_value_count": (
                unique_count
            ),
            "uniqueness_percentage": (
                uniqueness_percentage
            ),
        }

    return column_metrics


# ============================================================
# DATA QUALITY SUMMARY
# ============================================================

def calculate_data_quality_summary(
    dataframe: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Generate dataset-level data-quality metrics.
    """

    safe_dataframe = make_dataframe_hashable(
        dataframe
    )

    total_rows = len(dataframe)

    total_cells = int(
        dataframe.size
    )

    total_null_cells = int(
        dataframe.isnull().sum().sum()
    )

    duplicate_rows = int(
        safe_dataframe.duplicated().sum()
    )

    overall_null_percentage = (
        round(
            (
                total_null_cells
                / total_cells
            )
            * 100,
            2,
        )
        if total_cells > 0
        else 0.0
    )

    duplicate_percentage = (
        round(
            (
                duplicate_rows
                / total_rows
            )
            * 100,
            2,
        )
        if total_rows > 0
        else 0.0
    )

    columns_with_nulls = int(
        (
            dataframe.isnull().sum()
            > 0
        ).sum()
    )

    return {
        "total_cells": total_cells,
        "total_null_cells": (
            total_null_cells
        ),
        "overall_null_percentage": (
            overall_null_percentage
        ),
        "duplicate_rows": (
            duplicate_rows
        ),
        "duplicate_percentage": (
            duplicate_percentage
        ),
        "columns_with_nulls": (
            columns_with_nulls
        ),
    }


# ============================================================
# PRIMARY KEY VALIDATION
# ============================================================

def validate_primary_keys(
    dataframe: pd.DataFrame,
    safe_dataframe: pd.DataFrame,
    primary_keys: List[str],
    total_rows: int,
) -> List[Dict[str, Any]]:
    """
    Validate primary key completeness and uniqueness.

    Checks:
        - No null values in any PK column
        - No duplicate PK value combinations

    Returns traceable findings with finding_id, dataset,
    column/key, rule, severity, count, and evidence.
    """

    issues = []

    missing_columns = [
        column
        for column in primary_keys
        if column not in dataframe.columns
    ]

    if missing_columns:

        issues.append(
            {
                "issue_type": (
                    "PRIMARY_KEY_MISSING_COLUMNS"
                ),
                "severity": "HIGH",
                "column": ", ".join(
                    missing_columns
                ),
                "finding_id": (
                    f"PK-MISSING-{len(missing_columns)}"
                ),
                "rule": "primary_key_validation",
                "affected_records": total_rows,
                "evidence": (
                    "Primary key columns not found "
                    f"in dataset: {missing_columns}"
                ),
                "message": (
                    "Configured primary key columns "
                    f"{missing_columns} "
                    "were not found in the dataset."
                ),
            }
        )

        return issues

    null_counts = {
        column: int(
            dataframe[column].isnull().sum()
        )
        for column in primary_keys
    }

    total_null_pk = sum(
        null_counts.values()
    )

    if total_null_pk > 0:

        issues.append(
            {
                "issue_type": (
                    "PRIMARY_KEY_NULL"
                ),
                "severity": "HIGH",
                "column": ", ".join(
                    primary_keys
                ),
                "finding_id": "PK-NULL",
                "rule": "primary_key_validation",
                "affected_records": total_null_pk,
                "evidence": (
                    "Null values detected in primary key "
                    f"columns: {null_counts}"
                ),
                "message": (
                    f"{total_null_pk} records have "
                    "null values in primary key columns."
                ),
            }
        )

    if len(primary_keys) == 1:

        column = primary_keys[0]

        duplicate_count = int(
            safe_dataframe[column]
            .duplicated(keep=False)
            .sum()
        )

        if duplicate_count > 0:

            issues.append(
                {
                    "issue_type": (
                        "PRIMARY_KEY_DUPLICATE"
                    ),
                    "severity": "HIGH",
                    "column": column,
                    "finding_id": "PK-DUPLICATE",
                    "rule": "primary_key_validation",
                    "affected_records": (
                        duplicate_count
                    ),
                    "evidence": (
                        f"Duplicate values detected "
                        f"in primary key column '{column}'"
                    ),
                    "message": (
                        f"{duplicate_count} records have "
                        f"duplicate values in primary key "
                        f"column '{column}'."
                    ),
                }
            )

    else:

        duplicate_count = int(
            safe_dataframe[primary_keys]
            .duplicated(keep=False)
            .sum()
        )

        if duplicate_count > 0:

            issues.append(
                {
                    "issue_type": (
                        "PRIMARY_KEY_DUPLICATE"
                    ),
                    "severity": "HIGH",
                    "column": ", ".join(
                        primary_keys
                    ),
                    "finding_id": "PK-DUPLICATE-COMPOSITE",
                    "rule": "primary_key_validation",
                    "affected_records": (
                        duplicate_count
                    ),
                    "evidence": (
                        "Duplicate composite key values "
                        f"detected for columns: {primary_keys}"
                    ),
                    "message": (
                        f"{duplicate_count} records have "
                        "duplicate composite primary key values."
                    ),
                }
            )

    return issues


# ============================================================
# PROFILING ISSUE DETECTION
# ============================================================

def detect_profiling_issues(
    dataframe: pd.DataFrame,
    column_rules: Optional[Dict[str, str]] = None,
    primary_keys: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Detect important profiling observations.

    This function does not decide whether migration should
    succeed or fail.

    It identifies data-quality observations for future
    assessment, recommendation, technical reporting,
    and executive reporting modules.

    Args:
        dataframe: The dataset to profile.
        column_rules: Optional mapping of column names to semantic
            types. Supported values: required, optional, nullable,
            conditionally_required, primary_key, business_key,
            foreign_key. When absent, all columns are treated as
            UNKNOWN_SEMANTICS.
        primary_keys: Optional list of column names that form the
            primary key. When provided, PK completeness and
            uniqueness are validated.
    """

    safe_dataframe = make_dataframe_hashable(
        dataframe
    )

    issues = []

    total_rows = len(dataframe)

    # --------------------------------------------------------
    # EMPTY DATASET
    # --------------------------------------------------------

    if total_rows == 0:

        issues.append(
            {
                "issue_type": (
                    "EMPTY_DATASET"
                ),
                "severity": "HIGH",
                "column": None,
                "message": (
                    "The dataset contains "
                    "no records."
                ),
            }
        )

        return issues

    # --------------------------------------------------------
    # DUPLICATE ROWS
    # --------------------------------------------------------

    duplicate_rows = int(
        safe_dataframe.duplicated().sum()
    )

    if duplicate_rows > 0:

        duplicate_percentage = round(
            (
                duplicate_rows
                / total_rows
            )
            * 100,
            2,
        )

        severity = (
            "HIGH"
            if duplicate_percentage >= 10
            else "MEDIUM"
        )

        issues.append(
            {
                "issue_type": (
                    "DUPLICATE_ROWS"
                ),
                "severity": severity,
                "column": None,
                "affected_records": (
                    duplicate_rows
                ),
                "affected_percentage": (
                    duplicate_percentage
                ),
                "message": (
                    f"{duplicate_rows} "
                    "duplicate records "
                    "were detected."
                ),
            }
        )

    # --------------------------------------------------------
    # PRIMARY KEY VALIDATION
    # --------------------------------------------------------

    if primary_keys:

        pk_issues = validate_primary_keys(
            dataframe,
            safe_dataframe,
            primary_keys,
            total_rows,
        )

        issues.extend(pk_issues)

    # --------------------------------------------------------
    # COLUMN NULL ANALYSIS
    # --------------------------------------------------------

    for column_name in dataframe.columns:

        column = dataframe[
            column_name
        ]

        null_count = int(
            column.isnull().sum()
        )

        if null_count == 0:
            continue

        null_percentage = round(
            (
                null_count
                / total_rows
            )
            * 100,
            2,
        )

        semantic = (
            column_rules.get(
                column_name,
                "UNKNOWN",
            )
            if column_rules
            else "UNKNOWN"
        )

        if semantic in (
            "required",
            "conditionally_required",
            "primary_key",
            "business_key",
        ):

            if null_percentage >= 80:

                severity = "HIGH"

            elif null_percentage >= 30:

                severity = "MEDIUM"

            else:

                severity = "LOW"

            issues.append(
                {
                    "issue_type": (
                        "NULL_VALUES"
                    ),
                    "severity": severity,
                    "column": str(
                        column_name
                    ),
                    "affected_records": (
                        null_count
                    ),
                    "affected_percentage": (
                        null_percentage
                    ),
                    "message": (
                        f"Column '{column_name}' "
                        f"contains "
                        f"{null_percentage}% "
                        "null values."
                    ),
                }
            )

        elif semantic == "optional":

            if null_percentage >= 95:

                continue

            if null_percentage >= 80:

                severity = "LOW"

            else:

                severity = "LOW"

            issues.append(
                {
                    "issue_type": (
                        "NULL_VALUES_OPTIONAL"
                    ),
                    "severity": severity,
                    "column": str(
                        column_name
                    ),
                    "affected_records": (
                        null_count
                    ),
                    "affected_percentage": (
                        null_percentage
                    ),
                    "message": (
                        f"Optional column '{column_name}' "
                        f"contains "
                        f"{null_percentage}% "
                        "null values."
                    ),
                }
            )

        else:

            pass

    # --------------------------------------------------------
    # CONSTANT COLUMN ANALYSIS
    # --------------------------------------------------------

    for column_name in dataframe.columns:

        original_column = dataframe[
            column_name
        ]

        safe_column = safe_dataframe[
            column_name
        ]

        non_null_count = int(
            original_column.notnull().sum()
        )

        unique_count = int(
            safe_column.nunique(
                dropna=True
            )
        )

        if (
            non_null_count > 0
            and unique_count == 1
        ):

            issues.append(
                {
                    "issue_type": (
                        "CONSTANT_COLUMN"
                    ),
                    "severity": "LOW",
                    "column": str(
                        column_name
                    ),
                    "affected_records": (
                        non_null_count
                    ),
                    "message": (
                        f"Column "
                        f"'{column_name}' "
                        "contains only one "
                        "unique non-null value."
                    ),
                }
            )

    return issues


# ============================================================
# PROFILING ISSUE SUMMARY
# ============================================================

def summarize_profiling_issues(
    issues: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Generate a severity-based profiling issue summary.
    """

    high_issues = 0
    medium_issues = 0
    low_issues = 0

    for issue in issues:

        severity = issue.get(
            "severity"
        )

        if severity == "HIGH":

            high_issues += 1

        elif severity == "MEDIUM":

            medium_issues += 1

        elif severity == "LOW":

            low_issues += 1

    return {
        "total_issues": len(issues),
        "high_severity_issues": (
            high_issues
        ),
        "medium_severity_issues": (
            medium_issues
        ),
        "low_severity_issues": (
            low_issues
        ),
    }