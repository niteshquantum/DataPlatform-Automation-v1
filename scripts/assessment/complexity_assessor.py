"""
Migration Complexity Assessment Module.

Calculates migration complexity using:

- Source Data Volume
- Dataset Count
- Schema Width
- Reconciliation Findings
- Database Growth

The module remains database-independent.
"""

from typing import Any, Dict, List


# ============================================================
# COMPLEXITY LEVEL DETERMINATION
# ============================================================

def determine_complexity_level(
    complexity_score: int,
) -> str:

    if complexity_score >= 70:
        return "VERY_HIGH"

    if complexity_score >= 45:
        return "HIGH"

    if complexity_score >= 20:
        return "MEDIUM"

    return "LOW"


# ============================================================
# DATA VOLUME COMPLEXITY
# ============================================================

def calculate_volume_score(
    total_rows: int,
) -> int:

    if total_rows >= 10_000_000:
        return 30

    if total_rows >= 1_000_000:
        return 20

    if total_rows >= 100_000:
        return 10

    return 5


# ============================================================
# DATASET COUNT COMPLEXITY
# ============================================================

def calculate_dataset_score(
    total_datasets: int,
) -> int:

    if total_datasets >= 100:
        return 25

    if total_datasets >= 50:
        return 20

    if total_datasets >= 20:
        return 15

    if total_datasets >= 10:
        return 10

    return 5


# ============================================================
# SCHEMA WIDTH COMPLEXITY
# ============================================================

def calculate_schema_score(
    total_columns: int,
) -> int:

    if total_columns >= 1000:
        return 20

    if total_columns >= 500:
        return 15

    if total_columns >= 200:
        return 10

    return 5


# ============================================================
# RECONCILIATION COMPLEXITY
# ============================================================

def calculate_reconciliation_score(
    reconciliation_summary: Dict[str, Any],
) -> int:

    missing_datasets = int(
        reconciliation_summary.get(
            "missing_target_datasets",
            0,
        )
    )

    extra_datasets = int(
        reconciliation_summary.get(
            "extra_target_datasets",
            0,
        )
    )

    not_reconciled = int(
        reconciliation_summary.get(
            "not_reconciled_datasets",
            0,
        )
    )

    score = 0

    score += min(
        missing_datasets * 5,
        15,
    )

    score += min(
        extra_datasets * 2,
        10,
    )

    score += min(
        not_reconciled * 3,
        15,
    )

    return score


# ============================================================
# GROWTH COMPLEXITY
# ============================================================

def calculate_growth_score(
    growth_analysis: Dict[str, Any],
) -> int:

    if growth_analysis.get(
        "growth_status"
    ) != "ANALYZED":

        return 0

    growth_rate = (
        growth_analysis.get(
            "summary",
            {},
        ).get(
            "overall_growth_rate_percent"
        )
    )

    if growth_rate is None:
        return 0

    growth_rate = float(growth_rate)

    if growth_rate >= 50:
        return 15

    if growth_rate >= 20:
        return 10

    if growth_rate >= 10:
        return 5

    return 0


# ============================================================
# COMPLEXITY ASSESSMENT
# ============================================================

def assess_complexity(
    profiling_summary: Dict[str, Any],
    reconciliation_summary: Dict[str, Any],
    discovery_summary: Dict[str, Any],
    growth_analysis: Dict[str, Any],
) -> Dict[str, Any]:

    # Existing profiling values

    total_rows = int(
        profiling_summary.get(
            "total_rows",
            0,
        )
    )

    total_datasets = int(
        profiling_summary.get(
            "total_files_found",
            0,
        )
    )

    total_columns = int(
        profiling_summary.get(
            "total_columns",
            0,
        )
    )

    # Discovery database values

    discovered_total_records = int(
        discovery_summary.get(
            "total_records",
            0,
        )
    )

    discovered_total_datasets = int(
        discovery_summary.get(
            "total_datasets",
            0,
        )
    )

    volume_score = calculate_volume_score(
        total_rows
    )

    dataset_score = calculate_dataset_score(
        total_datasets
    )

    schema_score = calculate_schema_score(
        total_columns
    )

    reconciliation_score = (
        calculate_reconciliation_score(
            reconciliation_summary
        )
    )

    growth_score = calculate_growth_score(
        growth_analysis
    )

    total_complexity_score = (
        volume_score
        + dataset_score
        + schema_score
        + reconciliation_score
        + growth_score
    )

    complexity_level = determine_complexity_level(
        total_complexity_score
    )

    complexity_factors: List[
        Dict[str, Any]
    ] = []

    complexity_factors.append(
        {
            "factor": "DATA_VOLUME",
            "score": volume_score,
            "observed_value": total_rows,
            "message": (
                f"Source datasets contain "
                f"{total_rows} total records."
            ),
        }
    )

    complexity_factors.append(
        {
            "factor": "DATASET_COUNT",
            "score": dataset_score,
            "observed_value": total_datasets,
            "message": (
                f"{total_datasets} source datasets "
                "are included in the migration scope."
            ),
        }
    )

    complexity_factors.append(
        {
            "factor": "SCHEMA_WIDTH",
            "score": schema_score,
            "observed_value": total_columns,
            "message": (
                f"Source datasets contain "
                f"{total_columns} total columns."
            ),
        }
    )

    complexity_factors.append(
        {
            "factor": "DATABASE_DISCOVERY",
            "score": 0,
            "observed_value": {
                "total_datasets": (
                    discovered_total_datasets
                ),
                "total_records": (
                    discovered_total_records
                ),
            },
            "message": (
                "Database discovery identified "
                f"{discovered_total_datasets} datasets "
                f"containing {discovered_total_records} "
                "total records."
            ),
        }
    )

    if reconciliation_score > 0:

        complexity_factors.append(
            {
                "factor": "RECONCILIATION_FINDINGS",
                "score": reconciliation_score,
                "observed_value": {
                    "missing_target_datasets": (
                        reconciliation_summary.get(
                            "missing_target_datasets",
                            0,
                        )
                    ),
                    "extra_target_datasets": (
                        reconciliation_summary.get(
                            "extra_target_datasets",
                            0,
                        )
                    ),
                    "not_reconciled_datasets": (
                        reconciliation_summary.get(
                            "not_reconciled_datasets",
                            0,
                        )
                    ),
                },
                "message": (
                    "Source-to-target reconciliation "
                    "findings increase migration complexity."
                ),
            }
        )

    if growth_score > 0:

        complexity_factors.append(
            {
                "factor": "DATABASE_GROWTH",
                "score": growth_score,
                "observed_value": (
                    growth_analysis.get(
                        "summary",
                        {},
                    ).get(
                        "overall_growth_rate_percent"
                    )
                ),
                "message": (
                    "Database growth increases "
                    "migration complexity."
                ),
            }
        )

    return {
        "complexity_score": (
            total_complexity_score
        ),
        "complexity_level": (
            complexity_level
        ),
        "complexity_score_breakdown": {
            "data_volume_score": volume_score,
            "dataset_count_score": dataset_score,
            "schema_width_score": schema_score,
            "reconciliation_score": (
                reconciliation_score
            ),
            "growth_score": growth_score,
        },
        "database_discovery_summary": {
            "total_datasets": (
                discovered_total_datasets
            ),
            "total_records": (
                discovered_total_records
            ),
        },
        "complexity_factors": (
            complexity_factors
        ),
    }