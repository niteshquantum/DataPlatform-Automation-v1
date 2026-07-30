"""
Migration Readiness Assessment Module.

Calculates migration readiness using:

- Profiling Findings
- Reconciliation Findings
- Migration Risk
- Migration Complexity
- Retention Requirements
- SLA Requirements
"""

from typing import Any, Dict, List


# ============================================================
# READINESS LEVEL DETERMINATION
# ============================================================

def determine_readiness_level(
    readiness_score: int,
) -> str:

    if readiness_score >= 85:
        return "READY"

    if readiness_score >= 65:
        return "READY_WITH_CONDITIONS"

    if readiness_score >= 40:
        return "NEEDS_REMEDIATION"

    return "NOT_READY"


# ============================================================
# PROFILING PENALTY
# ============================================================

def calculate_profiling_penalty(
    profiling_summary: Dict[str, Any],
) -> int:

    high_issues = int(
        profiling_summary.get(
            "high_severity_issues",
            0,
        )
    )

    medium_issues = int(
        profiling_summary.get(
            "medium_severity_issues",
            0,
        )
    )

    low_issues = int(
        profiling_summary.get(
            "low_severity_issues",
            0,
        )
    )

    penalty = (
        high_issues * 8
        + medium_issues * 4
        + low_issues
    )

    return min(penalty, 35)


# ============================================================
# RECONCILIATION PENALTY
# ============================================================

def calculate_reconciliation_penalty(
    reconciliation_summary: Dict[str, Any],
) -> Dict[str, Any]:

    reconciliation_status = (
        reconciliation_summary.get(
            "reconciliation_status",
            "EXECUTED",
        )
    )

    if reconciliation_status == (
        "NOT_EXECUTED_DATABASE_REQUIRED"
    ):

        return {
            "penalty": 0,
            "reconciliation_status": (
                "NOT_EXECUTED_DATABASE_REQUIRED"
            ),
            "message": (
                "Reconciliation was not executed because "
                "the target database was unavailable. "
                "No penalty applied."
            ),
        }

    high_issues = int(
        reconciliation_summary.get(
            "high_severity_issues",
            0,
        )
    )

    medium_issues = int(
        reconciliation_summary.get(
            "medium_severity_issues",
            0,
        )
    )

    low_issues = int(
        reconciliation_summary.get(
            "low_severity_issues",
            0,
        )
    )

    missing_datasets = int(
        reconciliation_summary.get(
            "missing_target_datasets",
            0,
        )
    )

    not_reconciled = int(
        reconciliation_summary.get(
            "not_reconciled_datasets",
            0,
        )
    )

    penalty = (
        high_issues * 10
        + medium_issues * 5
        + low_issues * 2
        + missing_datasets * 5
        + not_reconciled * 3
    )

    return {
        "penalty": min(penalty, 45),
        "reconciliation_status": "EXECUTED",
        "message": (
            "Source-to-target reconciliation "
            "findings reduce migration readiness."
        ),
    }


# ============================================================
# RISK PENALTY
# ============================================================

def calculate_risk_penalty(
    risk_assessment: Dict[str, Any],
) -> int:

    risk_level = risk_assessment.get(
        "risk_level",
        "LOW",
    )

    risk_penalties = {
        "LOW": 0,
        "MEDIUM": 5,
        "HIGH": 10,
        "CRITICAL": 15,
    }

    return risk_penalties.get(
        risk_level,
        0,
    )


# ============================================================
# COMPLEXITY PENALTY
# ============================================================

def calculate_complexity_penalty(
    complexity_assessment: Dict[str, Any],
) -> int:

    complexity_level = (
        complexity_assessment.get(
            "complexity_level",
            "LOW",
        )
    )

    complexity_penalties = {
        "LOW": 0,
        "MEDIUM": 3,
        "HIGH": 6,
        "VERY_HIGH": 10,
    }

    return complexity_penalties.get(
        complexity_level,
        0,
    )


# ============================================================
# REQUIREMENT PENALTY
# ============================================================

def calculate_requirement_penalty(
    requirements_analysis: Dict[str, Any],
) -> Dict[str, Any]:

    retention = requirements_analysis.get(
        "retention_requirements",
        {},
    )

    sla = requirements_analysis.get(
        "sla_requirements",
        {},
    )

    retention_days = int(
        retention.get(
            "required_retention_days",
            0,
        )
    )

    archive_required = bool(
        retention.get(
            "archive_required",
            False,
        )
    )

    migration_duration = int(
        sla.get(
            "maximum_migration_duration_minutes",
            0,
        )
    )

    maximum_downtime = int(
        sla.get(
            "maximum_downtime_minutes",
            0,
        )
    )

    has_duration_sla = migration_duration > 0
    has_downtime_sla = maximum_downtime > 0

    if not has_duration_sla and not has_downtime_sla:

        retention_penalty = 0
        sla_penalty = 0

        return {
            "retention_penalty": 0,
            "sla_penalty": 0,
        }

    retention_penalty = 0
    sla_penalty = 0

    if retention_days >= 2555:
        retention_penalty += 5

    elif retention_days >= 1095:
        retention_penalty += 3

    if archive_required:
        retention_penalty += 2

    if has_duration_sla:

        if migration_duration <= 30:
            sla_penalty += 5

        elif migration_duration <= 120:
            sla_penalty += 3

    if has_downtime_sla:

        if maximum_downtime <= 5:
            sla_penalty += 5

        elif maximum_downtime <= 30:
            sla_penalty += 3

    return {
        "retention_penalty": min(
            retention_penalty,
            7,
        ),
        "sla_penalty": min(
            sla_penalty,
            10,
        ),
    }


# ============================================================
# READINESS ASSESSMENT
# ============================================================

def assess_readiness(
    profiling_summary: Dict[str, Any],
    reconciliation_summary: Dict[str, Any],
    risk_assessment: Dict[str, Any],
    complexity_assessment: Dict[str, Any],
    requirements_analysis: Dict[str, Any],
) -> Dict[str, Any]:

    base_score = 100

    profiling_penalty = (
        calculate_profiling_penalty(
            profiling_summary
        )
    )

    reconciliation_penalty_result = (
        calculate_reconciliation_penalty(
            reconciliation_summary
        )
    )

    reconciliation_penalty = (
        reconciliation_penalty_result["penalty"]
    )

    risk_penalty = calculate_risk_penalty(
        risk_assessment
    )

    complexity_penalty = (
        calculate_complexity_penalty(
            complexity_assessment
        )
    )

    requirement_penalties = (
        calculate_requirement_penalty(
            requirements_analysis
        )
    )

    retention_penalty = (
        requirement_penalties[
            "retention_penalty"
        ]
    )

    sla_penalty = (
        requirement_penalties[
            "sla_penalty"
        ]
    )

    total_penalty = (
        profiling_penalty
        + reconciliation_penalty
        + risk_penalty
        + complexity_penalty
        + retention_penalty
        + sla_penalty
    )

    readiness_score = max(
        0,
        base_score - total_penalty,
    )

    readiness_level = (
        determine_readiness_level(
            readiness_score
        )
    )

    readiness_factors: List[
        Dict[str, Any]
    ] = []

    if profiling_penalty > 0:

        readiness_factors.append(
            {
                "factor": "DATA_QUALITY",
                "penalty": profiling_penalty,
                "message": (
                    "Source data-quality findings "
                    "reduce migration readiness."
                ),
            }
        )

    if reconciliation_penalty > 0:

        readiness_factors.append(
            {
                "factor": "RECONCILIATION",
                "penalty": reconciliation_penalty,
                "message": (
                    "Source-to-target reconciliation "
                    "findings reduce migration readiness."
                ),
            }
        )

    elif (
        reconciliation_penalty_result.get(
            "reconciliation_status"
        )
        == "NOT_EXECUTED_DATABASE_REQUIRED"
    ):

        readiness_factors.append(
            {
                "factor": "RECONCILIATION",
                "penalty": 0,
                "message": (
                    "Reconciliation was not executed "
                    "because the target database was "
                    "unavailable. No penalty applied."
                ),
                "status": "NOT_EXECUTED_DATABASE_REQUIRED",
            }
        )

    if risk_penalty > 0:

        readiness_factors.append(
            {
                "factor": "MIGRATION_RISK",
                "penalty": risk_penalty,
                "message": (
                    "The assessed migration risk level "
                    "reduces migration readiness."
                ),
            }
        )

    if complexity_penalty > 0:

        readiness_factors.append(
            {
                "factor": "MIGRATION_COMPLEXITY",
                "penalty": complexity_penalty,
                "message": (
                    "The assessed migration complexity "
                    "reduces migration readiness."
                ),
            }
        )

    if retention_penalty > 0:

        readiness_factors.append(
            {
                "factor": "RETENTION_REQUIREMENTS",
                "penalty": retention_penalty,
                "message": (
                    "Data retention and archival "
                    "requirements reduce migration readiness."
                ),
            }
        )

    if sla_penalty > 0:

        readiness_factors.append(
            {
                "factor": "SLA_REQUIREMENTS",
                "penalty": sla_penalty,
                "message": (
                    "Migration duration and downtime "
                    "requirements reduce migration readiness."
                ),
            }
        )

    return {
        "readiness_score": readiness_score,
        "readiness_level": readiness_level,
        "base_score": base_score,
        "total_penalty": total_penalty,
        "readiness_score_breakdown": {
            "profiling_penalty": profiling_penalty,
            "reconciliation_penalty": (
                reconciliation_penalty
            ),
            "risk_penalty": risk_penalty,
            "complexity_penalty": (
                complexity_penalty
            ),
            "retention_penalty": (
                retention_penalty
            ),
            "sla_penalty": sla_penalty,
        },
        "readiness_factors": readiness_factors,
    }