"""
Common reconciliation metric utilities.

This module contains reusable functions for comparing expected
source/incoming dataset information with actual loaded database
results.

It is database-independent and supports MySQL, PostgreSQL,
MSSQL, and MongoDB reconciliation workflows.
"""

from typing import Any, Dict, List


# ============================================================
# ROW COUNT RECONCILIATION
# ============================================================

def reconcile_row_counts(
    expected_rows: int,
    actual_rows: int,
) -> Dict[str, Any]:
    """
    Compare expected source rows with actual loaded rows.
    """

    row_difference = actual_rows - expected_rows

    absolute_difference = abs(row_difference)

    if expected_rows > 0:

        match_percentage = round(
            (
                min(expected_rows, actual_rows)
                / max(expected_rows, actual_rows)
            )
            * 100,
            2,
        )

    elif actual_rows == 0:

        match_percentage = 100.0

    else:

        match_percentage = 0.0

    if expected_rows == actual_rows:

        status = "MATCHED"

    else:

        status = "MISMATCHED"

    return {
        "expected_rows": expected_rows,
        "actual_rows": actual_rows,
        "row_difference": row_difference,
        "absolute_difference": absolute_difference,
        "match_percentage": match_percentage,
        "status": status,
    }


# ============================================================
# COLUMN COUNT RECONCILIATION
# ============================================================

def reconcile_column_counts(
    expected_columns: int,
    actual_columns: int,
) -> Dict[str, Any]:
    """
    Compare expected source column count with target column count.
    """

    column_difference = (
        actual_columns - expected_columns
    )

    absolute_difference = abs(
        column_difference
    )

    if expected_columns == actual_columns:

        status = "MATCHED"

    else:

        status = "MISMATCHED"

    return {
        "expected_columns": expected_columns,
        "actual_columns": actual_columns,
        "column_difference": column_difference,
        "absolute_difference": absolute_difference,
        "status": status,
    }


# ============================================================
# RECONCILIATION ISSUE DETECTION
# ============================================================

def detect_reconciliation_issues(
    dataset_name: str,
    row_reconciliation: Dict[str, Any],
    column_reconciliation: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Detect reconciliation issues for one dataset.

    These issues will later be consumed by the Assessment,
    Recommendation, Technical Reporting, and Executive
    Reporting modules.
    """

    issues = []

    # --------------------------------------------------------
    # ROW COUNT MISMATCH
    # --------------------------------------------------------

    if row_reconciliation["status"] == "MISMATCHED":

        match_percentage = row_reconciliation[
            "match_percentage"
        ]

        if match_percentage < 90:

            severity = "HIGH"

        elif match_percentage < 99:

            severity = "MEDIUM"

        else:

            severity = "LOW"

        issues.append(
            {
                "issue_type": "ROW_COUNT_MISMATCH",
                "severity": severity,
                "dataset": dataset_name,
                "expected_rows": row_reconciliation[
                    "expected_rows"
                ],
                "actual_rows": row_reconciliation[
                    "actual_rows"
                ],
                "difference": row_reconciliation[
                    "row_difference"
                ],
                "match_percentage": match_percentage,
                "message": (
                    f"Dataset '{dataset_name}' contains "
                    "a row count mismatch between the "
                    "expected source data and loaded target data."
                ),
            }
        )

    # --------------------------------------------------------
    # COLUMN COUNT MISMATCH
    # --------------------------------------------------------

    if column_reconciliation["status"] == "MISMATCHED":

        absolute_difference = column_reconciliation.get(
            "absolute_difference",
            0,
        )

        if absolute_difference <= 2:

            severity = "MEDIUM"
            issue_type = "COLUMN_COUNT_MISMATCH_MINOR"

        else:

            severity = "HIGH"
            issue_type = "COLUMN_COUNT_MISMATCH"

        issues.append(
            {
                "issue_type": issue_type,
                "severity": severity,
                "dataset": dataset_name,
                "expected_columns": column_reconciliation[
                    "expected_columns"
                ],
                "actual_columns": column_reconciliation[
                    "actual_columns"
                ],
                "difference": column_reconciliation[
                    "column_difference"
                ],
                "message": (
                    f"Dataset '{dataset_name}' contains "
                    "a column count mismatch between the "
                    "expected source structure and loaded "
                    "target structure."
                ),
            }
        )

    return issues


# ============================================================
# RECONCILIATION STATUS
# ============================================================

def determine_reconciliation_status(
    row_reconciliation: Dict[str, Any],
    column_reconciliation: Dict[str, Any],
) -> str:
    """
    Determine the overall reconciliation status of one dataset.
    """

    if (
        row_reconciliation["status"] == "MATCHED"
        and column_reconciliation["status"] == "MATCHED"
    ):

        return "RECONCILED"

    return "NOT_RECONCILED"


# ============================================================
# RECONCILIATION ISSUE SUMMARY
# ============================================================

def summarize_reconciliation_issues(
    issues: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Generate a severity-based reconciliation issue summary.
    """

    high_issues = 0
    medium_issues = 0
    low_issues = 0

    for issue in issues:

        severity = issue.get("severity")

        if severity == "HIGH":

            high_issues += 1

        elif severity == "MEDIUM":

            medium_issues += 1

        elif severity == "LOW":

            low_issues += 1

    return {
        "total_issues": len(issues),
        "high_severity_issues": high_issues,
        "medium_severity_issues": medium_issues,
        "low_severity_issues": low_issues,
    }