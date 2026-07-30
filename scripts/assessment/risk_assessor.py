"""
Migration Risk Assessment Module.

Calculates migration risk using:

- Data Profiling Findings
- Source-to-Target Reconciliation Findings
- Database Growth Findings
- Retention Requirements
- SLA Requirements

The module remains database-independent.
"""

from typing import Any, Dict, List


# ============================================================
# RISK WEIGHTS
# ============================================================

SEVERITY_WEIGHTS = {
    "HIGH": 10,
    "MEDIUM": 5,
    "LOW": 2,
}


# ============================================================
# ISSUE SCORE CALCULATION
# ============================================================

def calculate_issue_score(
    high_issues: int,
    medium_issues: int,
    low_issues: int,
) -> int:

    return (
        high_issues * SEVERITY_WEIGHTS["HIGH"]
        + medium_issues * SEVERITY_WEIGHTS["MEDIUM"]
        + low_issues * SEVERITY_WEIGHTS["LOW"]
    )


# ============================================================
# RISK LEVEL DETERMINATION
# ============================================================

def determine_risk_level(
    risk_score: int,
) -> str:

    if risk_score >= 50:
        return "CRITICAL"

    if risk_score >= 25:
        return "HIGH"

    if risk_score >= 10:
        return "MEDIUM"

    return "LOW"


# ============================================================
# GROWTH RISK
# ============================================================

def calculate_growth_risk(
    growth_analysis: Dict[str, Any],
) -> Dict[str, Any]:

    growth_status = growth_analysis.get(
        "growth_status",
        "UNKNOWN",
    )

    summary = growth_analysis.get(
        "summary",
        {},
    )

    if growth_status == "BASELINE_CREATED":

        return {
            "score": 0,
            "severity": "LOW",
            "message": (
                "Growth baseline has been created. "
                "Historical growth risk is not yet available."
            ),
        }

    growth_rate = summary.get(
        "overall_growth_rate_percent"
    )

    if growth_rate is None:

        return {
            "score": 0,
            "severity": "LOW",
            "message": (
                "Growth rate is not currently available."
            ),
        }

    growth_rate = float(growth_rate)

    if growth_rate >= 50:

        return {
            "score": 15,
            "severity": "HIGH",
            "message": (
                "Very high database growth was detected."
            ),
        }

    if growth_rate >= 20:

        return {
            "score": 10,
            "severity": "HIGH",
            "message": (
                "High database growth was detected."
            ),
        }

    if growth_rate >= 10:

        return {
            "score": 5,
            "severity": "MEDIUM",
            "message": (
                "Moderate database growth was detected."
            ),
        }

    return {
        "score": 0,
        "severity": "LOW",
        "message": (
            "Database growth is within the "
            "configured assessment threshold."
        ),
    }


# ============================================================
# RETENTION RISK
# ============================================================

def calculate_retention_risk(
    requirements_analysis: Dict[str, Any],
) -> Dict[str, Any]:

    retention = requirements_analysis.get(
        "retention_requirements",
        {},
    )

    required_retention_days = int(
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

    if (
        required_retention_days >= 2555
        and archive_required
    ):

        return {
            "score": 10,
            "severity": "HIGH",
            "message": (
                "Long-term data retention and archival "
                "requirements increase migration risk."
            ),
        }

    if (
        required_retention_days >= 1095
        or archive_required
    ):

        return {
            "score": 5,
            "severity": "MEDIUM",
            "message": (
                "Data retention or archival requirements "
                "require migration planning controls."
            ),
        }

    return {
        "score": 0,
        "severity": "LOW",
        "message": (
            "Retention requirements introduce "
            "limited migration risk."
        ),
    }


# ============================================================
# SLA RISK
# ============================================================

def calculate_sla_risk(
    requirements_analysis: Dict[str, Any],
) -> Dict[str, Any]:

    sla = requirements_analysis.get(
        "sla_requirements",
        {},
    )

    maximum_migration_duration = int(
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

    has_duration_sla = maximum_migration_duration > 0
    has_downtime_sla = maximum_downtime > 0

    if not has_duration_sla and not has_downtime_sla:

        return {
            "score": 0,
            "severity": "LOW",
            "sla_status": "NOT_APPLICABLE",
            "message": (
                "No SLA requirements are configured. "
                "SLA risk is not applicable."
            ),
        }

    score = 0
    severity = "LOW"
    messages = []

    if has_duration_sla:

        if maximum_migration_duration <= 30:

            score = 10
            severity = "HIGH"
            messages.append(
                "Strict migration duration SLA "
                "increases migration execution risk."
            )

        elif maximum_migration_duration <= 120:

            score = 5
            severity = "MEDIUM"
            messages.append(
                "Migration duration SLA requirements "
                "require controlled execution planning."
            )

    if has_downtime_sla:

        if maximum_downtime <= 5:

            score = max(score, 10)
            severity = "HIGH"
            messages.append(
                "Strict downtime SLA "
                "increases migration execution risk."
            )

        elif maximum_downtime <= 30:

            score = max(score, 5)
            severity = "MEDIUM"
            messages.append(
                "Downtime SLA requirements "
                "require controlled execution planning."
            )

    return {
        "score": score,
        "severity": severity,
        "sla_status": "CONFIGURED",
        "message": (
            " ".join(messages)
            if messages
            else (
                "Configured SLA requirements introduce "
                "limited migration risk."
            )
        ),
    }


# ============================================================
# RISK ASSESSMENT
# ============================================================

def assess_risk(
    profiling_summary: Dict[str, Any],
    reconciliation_summary: Dict[str, Any],
    growth_analysis: Dict[str, Any],
    requirements_analysis: Dict[str, Any],
) -> Dict[str, Any]:

    # --------------------------------------------------------
    # PROFILING RISK SCORE (INFORMATIONAL ONLY)
    # --------------------------------------------------------
    # Profiling findings contribute to readiness penalty
    # through assess_readiness(), not to risk score.
    # Retained here for transparency and reporting only.

    profiling_high = int(
        profiling_summary.get(
            "high_severity_issues",
            0,
        )
    )

    profiling_medium = int(
        profiling_summary.get(
            "medium_severity_issues",
            0,
        )
    )

    profiling_low = int(
        profiling_summary.get(
            "low_severity_issues",
            0,
        )
    )

    profiling_risk_score = 0

    # --------------------------------------------------------
    # RECONCILIATION FINDINGS
    # --------------------------------------------------------

    reconciliation_high = int(
        reconciliation_summary.get(
            "high_severity_issues",
            0,
        )
    )

    reconciliation_medium = int(
        reconciliation_summary.get(
            "medium_severity_issues",
            0,
        )
    )

    reconciliation_low = int(
        reconciliation_summary.get(
            "low_severity_issues",
            0,
        )
    )

    # --------------------------------------------------------
    # EXISTING RISK SCORES
    # --------------------------------------------------------

    profiling_risk_score = calculate_issue_score(
        profiling_high,
        profiling_medium,
        profiling_low,
    )

    reconciliation_risk_score = calculate_issue_score(
        reconciliation_high,
        reconciliation_medium,
        reconciliation_low,
    )

    # --------------------------------------------------------
    # DISCOVERY RISK SCORES
    # --------------------------------------------------------

    growth_risk = calculate_growth_risk(
        growth_analysis
    )

    retention_risk = calculate_retention_risk(
        requirements_analysis
    )

    sla_risk = calculate_sla_risk(
        requirements_analysis
    )

    discovery_risk_score = (
        growth_risk["score"]
        + retention_risk["score"]
        + sla_risk["score"]
    )

    # --------------------------------------------------------
    # TOTAL RISK
    # --------------------------------------------------------

    total_risk_score = (
        reconciliation_risk_score
        + discovery_risk_score
    )

    risk_level = determine_risk_level(
        total_risk_score
    )

    # --------------------------------------------------------
    # RISK FACTORS
    # --------------------------------------------------------

    risk_factors: List[Dict[str, Any]] = []

    if profiling_high > 0:

        risk_factors.append(
            {
                "source": "PROFILING",
                "severity": "HIGH",
                "issue_count": profiling_high,
                "message": (
                    "High-severity data quality issues "
                    "were detected in source datasets."
                ),
            }
        )

    if profiling_medium > 0:

        risk_factors.append(
            {
                "source": "PROFILING",
                "severity": "MEDIUM",
                "issue_count": profiling_medium,
                "message": (
                    "Medium-severity data quality issues "
                    "were detected in source datasets."
                ),
            }
        )

    if reconciliation_high > 0:

        risk_factors.append(
            {
                "source": "RECONCILIATION",
                "severity": "HIGH",
                "issue_count": reconciliation_high,
                "message": (
                    "High-severity source-to-target "
                    "reconciliation issues were detected."
                ),
            }
        )

    if reconciliation_medium > 0:

        risk_factors.append(
            {
                "source": "RECONCILIATION",
                "severity": "MEDIUM",
                "issue_count": reconciliation_medium,
                "message": (
                    "Medium-severity source-to-target "
                    "reconciliation issues were detected."
                ),
            }
        )

    if growth_risk["score"] > 0:

        risk_factors.append(
            {
                "source": "DISCOVERY_GROWTH",
                "severity": growth_risk[
                    "severity"
                ],
                "issue_count": 1,
                "message": growth_risk[
                    "message"
                ],
            }
        )

    if retention_risk["score"] > 0:

        risk_factors.append(
            {
                "source": "DISCOVERY_RETENTION",
                "severity": retention_risk[
                    "severity"
                ],
                "issue_count": 1,
                "message": retention_risk[
                    "message"
                ],
            }
        )

    if sla_risk["score"] > 0:

        risk_factors.append(
            {
                "source": "DISCOVERY_SLA",
                "severity": sla_risk[
                    "severity"
                ],
                "issue_count": 1,
                "message": sla_risk[
                    "message"
                ],
            }
        )

    # --------------------------------------------------------
    # OUTPUT
    # --------------------------------------------------------

    return {
        "risk_score": total_risk_score,
        "risk_level": risk_level,
        "risk_score_breakdown": {
            "profiling_risk_score": (
                profiling_risk_score
            ),
            "reconciliation_risk_score": (
                reconciliation_risk_score
            ),
            "discovery_risk_score": (
                discovery_risk_score
            ),
            "growth_risk_score": (
                growth_risk["score"]
            ),
            "retention_risk_score": (
                retention_risk["score"]
            ),
            "sla_risk_score": (
                sla_risk["score"]
            ),
        },
        "risk_issue_summary": {
            "high_severity_issues": (
                profiling_high
                + reconciliation_high
                + (
                    1
                    if growth_risk["severity"] == "HIGH"
                    and growth_risk["score"] > 0
                    else 0
                )
                + (
                    1
                    if retention_risk["severity"] == "HIGH"
                    and retention_risk["score"] > 0
                    else 0
                )
                + (
                    1
                    if sla_risk["severity"] == "HIGH"
                    and sla_risk["score"] > 0
                    else 0
                )
            ),
            "medium_severity_issues": (
                profiling_medium
                + reconciliation_medium
                + (
                    1
                    if growth_risk["severity"] == "MEDIUM"
                    and growth_risk["score"] > 0
                    else 0
                )
                + (
                    1
                    if retention_risk["severity"] == "MEDIUM"
                    and retention_risk["score"] > 0
                    else 0
                )
                + (
                    1
                    if sla_risk["severity"] == "MEDIUM"
                    and sla_risk["score"] > 0
                    else 0
                )
            ),
            "low_severity_issues": (
                profiling_low
                + reconciliation_low
            ),
        },
        "discovery_risk_assessment": {
            "growth": growth_risk,
            "retention": retention_risk,
            "sla": sla_risk,
        },
        "risk_factors": risk_factors,
    }