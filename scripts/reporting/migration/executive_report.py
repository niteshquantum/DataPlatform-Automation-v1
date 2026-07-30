"""
Migration Executive Report Generator.

Generates a business-focused HTML report for managers,
decision-makers, and non-technical stakeholders.

The report converts technical migration findings into:
    - Executive decision status
    - Migration health overview
    - Business concerns
    - Readiness information
    - Priority actions
    - Management recommendation

Generates:
    reports/migration/<database>/executive_report.html
"""

import argparse
import html
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


# ============================================================
# PROJECT ROOT AND IMPORT SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from scripts.reporting.migration.report_data_builder import (
    SUPPORTED_DATABASES,
    build_report_data,
)


# ============================================================
# HTML UTILITIES
# ============================================================

def escape_html(value: Any) -> str:
    """
    Convert a value into HTML-safe text.
    """

    if value is None:
        return "-"

    return html.escape(str(value))


def format_number(value: Any) -> str:
    """
    Format numeric values.
    """

    if value is None:
        return "-"

    try:
        return f"{int(value):,}"

    except (TypeError, ValueError):
        return escape_html(value)


def get_status_class(value: Any) -> str:
    """
    Return CSS class for business status values.
    """

    normalized_value = str(
        value or ""
    ).upper()

    success_values = {
        "READY",
        "LOW",
        "READY_FOR_NEXT_STAGE",
    }

    warning_values = {
        "MEDIUM",
        "READY_WITH_CONDITIONS",
        "CONDITIONAL_APPROVAL",
    }

    danger_values = {
        "HIGH",
        "CRITICAL",
        "VERY_HIGH",
        "NEEDS_REMEDIATION",
        "NOT_READY",
        "REMEDIATION_REQUIRED",
        "ACTION_REQUIRED",
    }

    if normalized_value in success_values:
        return "status-success"

    if normalized_value in warning_values:
        return "status-warning"

    if normalized_value in danger_values:
        return "status-danger"

    return "status-neutral"


def render_status_badge(value: Any) -> str:
    """
    Render business status badge.
    """

    return (
        f'<span class="status-badge '
        f'{get_status_class(value)}">'
        f'{escape_html(value)}'
        f'</span>'
    )


# ============================================================
# BUSINESS DECISION MESSAGE
# ============================================================

def build_decision_message(
    executive_summary: Dict[str, Any],
) -> Dict[str, str]:
    """
    Convert assessment result into a management-level decision.
    """

    readiness_level = executive_summary.get(
        "readiness_level"
    )

    if readiness_level == "READY":

        return {
            "title": "Migration Ready to Proceed",
            "message": (
                "The current migration assessment indicates "
                "that the data is ready to proceed to the "
                "next stage under standard migration controls."
            ),
            "decision": "PROCEED",
        }

    if readiness_level == "READY_WITH_CONDITIONS":

        return {
            "title": "Migration Can Proceed with Conditions",
            "message": (
                "The migration may proceed after defined "
                "conditions, ownership responsibilities, and "
                "remaining actions are formally documented."
            ),
            "decision": "CONDITIONAL PROCEED",
        }

    if readiness_level == "NEEDS_REMEDIATION":

        return {
            "title": "Remediation Required Before Approval",
            "message": (
                "The current assessment identified issues "
                "that should be addressed before final "
                "migration approval."
            ),
            "decision": "REMEDIATE BEFORE PROCEEDING",
        }

    return {
        "title": "Migration Not Ready",
        "message": (
            "The current migration condition requires "
            "significant corrective action before the "
            "migration should proceed."
        ),
        "decision": "DO NOT PROCEED",
    }


# ============================================================
# REPORT HEADER
# ============================================================

def build_report_header(
    report_data: Dict[str, Any],
    generated_at: str,
) -> str:
    """
    Build executive report header.
    """

    database = report_data[
        "database"
    ].upper()

    return f"""
    <header class="report-header">

        <div>

            <div class="report-label">
                DATA PLATFORM AUTOMATION
            </div>

            <h1>
                Migration Executive Assessment
            </h1>

            <p class="report-subtitle">
                Business-focused migration status,
                risk, readiness, and recommended actions.
            </p>

        </div>

        <div class="report-metadata">

            <div>
                <strong>Database</strong>
                <span>{escape_html(database)}</span>
            </div>

            <div>
                <strong>Generated At</strong>
                <span>{escape_html(generated_at)}</span>
            </div>

        </div>

    </header>
    """


# ============================================================
# EXECUTIVE DECISION SUMMARY
# ============================================================

def build_executive_decision(
    report_data: Dict[str, Any],
) -> str:
    """
    Build primary management decision section.
    """

    summary = report_data[
        "executive_summary"
    ]

    decision = build_decision_message(
        summary
    )

    return f"""
    <section class="decision-section">

        <div class="decision-label">
            MANAGEMENT DECISION
        </div>

        <h2>
            {escape_html(decision["title"])}
        </h2>

        <p class="decision-message">
            {escape_html(decision["message"])}
        </p>

        <div class="decision-result">
            {escape_html(decision["decision"])}
        </div>

    </section>
    """


# ============================================================
# MIGRATION HEALTH OVERVIEW
# ============================================================

def build_health_overview(
    report_data: Dict[str, Any],
) -> str:
    """
    Build migration health overview.
    """

    summary = report_data[
        "executive_summary"
    ]

    return f"""
    <section class="report-section">

        <h2>1. Migration Health Overview</h2>

        <p class="section-description">
            High-level indicators showing the current
            condition of the migration.
        </p>

        <div class="metric-grid">

            <div class="metric-card">

                <div class="metric-title">
                    Overall Status
                </div>

                <div class="metric-value">
                    {
                        render_status_badge(
                            summary.get(
                                "assessment_status"
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Migration Risk
                </div>

                <div class="metric-value">
                    {
                        render_status_badge(
                            summary.get(
                                "risk_level"
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Migration Complexity
                </div>

                <div class="metric-value">
                    {
                        render_status_badge(
                            summary.get(
                                "complexity_level"
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Readiness Score
                </div>

                <div class="readiness-score">
                    {
                        format_number(
                            summary.get(
                                "readiness_score"
                            )
                        )
                    }
                    <span>/ 100</span>
                </div>

                <div class="metric-value">
                    {
                        render_status_badge(
                            summary.get(
                                "readiness_level"
                            )
                        )
                    }
                </div>

            </div>

        </div>

    </section>
    """


# ============================================================
# DATA SCOPE
# ============================================================

def build_data_scope(
    report_data: Dict[str, Any],
) -> str:
    """
    Build business-readable migration data scope.
    """

    summary = report_data[
        "executive_summary"
    ]

    return f"""
    <section class="report-section">

        <h2>2. Migration Data Scope</h2>

        <p class="section-description">
            Summary of the data currently included in
            the migration assessment.
        </p>

        <div class="metric-grid">

            <div class="metric-card">

                <div class="metric-title">
                    Source Datasets
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "total_source_datasets"
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Source Records
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "total_source_rows"
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Data Quality Findings
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "total_data_quality_issues"
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Total Recommendations
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "total_recommendations"
                            )
                        )
                    }
                </div>

            </div>

        </div>

    </section>
    """

# ============================================================
# DATABASE DISCOVERY OVERVIEW
# ============================================================

def build_database_discovery_overview(
    report_data: Dict[str, Any],
) -> str:
    """
    Build management-level database discovery overview.
    """

    discovery = report_data.get(
        "discovery",
        {},
    )

    summary = discovery.get(
        "summary",
        {},
    )

    growth = discovery.get(
        "growth",
        {},
    )

    requirements = discovery.get(
        "requirements",
        {},
    )

    growth_summary = growth.get(
        "summary",
        {},
    )

    retention = requirements.get(
        "retention_requirements",
        {},
    )

    sla = requirements.get(
        "sla_requirements",
        {},
    )

    largest_datasets = summary.get(
        "largest_datasets",
        [],
    )

    largest_rows = []

    for dataset in largest_datasets[:5]:

        largest_rows.append(
            f"""
            <tr>
                <td>
                    {
                        escape_html(
                            dataset.get(
                                "dataset_name"
                            )
                        )
                    }
                </td>

                <td>
                    {
                        format_number(
                            dataset.get(
                                "record_count"
                            )
                        )
                    }
                </td>
            </tr>
            """
        )

    if largest_rows:

        largest_content = f"""
        <div class="table-container">

            <table>

                <thead>
                    <tr>
                        <th>Largest Database Dataset</th>
                        <th>Record Count</th>
                    </tr>
                </thead>

                <tbody>
                    {''.join(largest_rows)}
                </tbody>

            </table>

        </div>
        """

    else:

        largest_content = """
        <div class="positive-message">
            No database dataset information is available.
        </div>
        """

    return f"""
    <section class="report-section">

        <h2>3. Database Environment Overview</h2>

        <p class="section-description">
            Management-level overview of the current database
            environment, growth, retention, and migration
            service-level requirements.
        </p>

        <div class="metric-grid">

            <div class="metric-card">

                <div class="metric-title">
                    Database Datasets
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "total_datasets"
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Database Records
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "total_records"
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Record Growth
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            growth.get(
                                "record_growth",
                                0,
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Growth Rate
                </div>

                <div class="metric-number">
                    {
                        escape_html(
                            growth_summary.get(
                                "overall_growth_rate_percent",
                                0,
                            )
                        )
                    }%
                </div>

            </div>

        </div>

        <div class="metric-grid discovery-requirements">

            <div class="metric-card">

                <div class="metric-title">
                    Required Retention
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            retention.get(
                                "required_retention_days"
                            )
                        )
                    }
                </div>

                <div class="metric-value">
                    Days
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Archive Required
                </div>

                <div class="metric-number">
                    {
                        escape_html(
                            retention.get(
                                "archive_required"
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Maximum Migration Time
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            sla.get(
                                "maximum_migration_duration_minutes"
                            )
                        )
                    }
                </div>

                <div class="metric-value">
                    Minutes
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Maximum Downtime
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            sla.get(
                                "maximum_downtime_minutes"
                            )
                        )
                    }
                </div>

                <div class="metric-value">
                    Minutes
                </div>

            </div>

        </div>

        <h3>Largest Database Datasets</h3>

        {largest_content}

    </section>
    """
# ============================================================
# BUSINESS CONCERNS
# ============================================================

def build_business_concerns(
    report_data: Dict[str, Any],
) -> str:
    """
    Build business-facing concerns from priority recommendations.
    """

    recommendations = report_data[
        "recommendation"
    ][
        "recommendations"
    ]

    priority_recommendations = [
        recommendation
        for recommendation in recommendations
        if recommendation.get("priority")
        in ("CRITICAL", "HIGH")
    ]

    if not priority_recommendations:

        content = """
        <div class="positive-message">
            No critical or high-priority migration concerns
            were identified.
        </div>
        """

    else:

        concern_cards = []

        for recommendation in priority_recommendations:

            concern_cards.append(
                f"""
                <div class="concern-card">

                    <div class="concern-header">

                        <h3>
                            {
                                escape_html(
                                    recommendation.get(
                                        "title"
                                    )
                                )
                            }
                        </h3>

                        {
                            render_status_badge(
                                recommendation.get(
                                    "priority"
                                )
                            )
                        }

                    </div>

                    <div class="concern-block">

                        <strong>
                            What was identified?
                        </strong>

                        <p>
                            {
                                escape_html(
                                    recommendation.get(
                                        "finding"
                                    )
                                )
                            }
                        </p>

                    </div>

                    <div class="concern-block">

                        <strong>
                            Why does it matter?
                        </strong>

                        <p>
                            {
                                escape_html(
                                    recommendation.get(
                                        "business_impact"
                                    )
                                )
                            }
                        </p>

                    </div>

                </div>
                """
            )

        content = "".join(
            concern_cards
        )

    return f"""
    <section class="report-section">

        <h2>4. Key Business Concerns</h2>

        <p class="section-description">
            Highest-priority issues that may affect
            migration approval or business outcomes.
        </p>

        {content}

    </section>
    """


# ============================================================
# RECONCILIATION HEALTH
# ============================================================

def build_reconciliation_health(
    report_data: Dict[str, Any],
) -> str:
    """
    Build management-level reconciliation summary.
    """

    summary = report_data[
        "executive_summary"
    ]

    return f"""
    <section class="report-section">

        <h2>5. Migration Completeness</h2>

        <p class="section-description">
            Comparison between expected source datasets
            and data available in the target environment.
        </p>

        <div class="metric-grid">

            <div class="metric-card">

                <div class="metric-title">
                    Reconciled Datasets
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "reconciled_datasets"
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Not Reconciled
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "not_reconciled_datasets"
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Missing Targets
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "missing_target_datasets"
                            )
                        )
                    }
                </div>

            </div>

            <div class="metric-card">

                <div class="metric-title">
                    Unexpected Targets
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "extra_target_datasets"
                            )
                        )
                    }
                </div>

            </div>

        </div>

    </section>
    """


# ============================================================
# PRIORITY ACTIONS
# ============================================================

def build_priority_actions(
    report_data: Dict[str, Any],
) -> str:
    """
    Build management-facing prioritized action plan.
    """

    recommendations = report_data[
        "recommendation"
    ][
        "recommendations"
    ]

    priority_recommendations = [
        recommendation
        for recommendation in recommendations
        if recommendation.get("priority")
        in ("CRITICAL", "HIGH", "MEDIUM")
    ]

    if not priority_recommendations:

        content = """
        <div class="positive-message">
            No immediate corrective actions are required.
        </div>
        """

    else:

        rows = []

        for recommendation in priority_recommendations:

            rows.append(
                f"""
                <tr>

                    <td>
                        {
                            render_status_badge(
                                recommendation.get(
                                    "priority"
                                )
                            )
                        }
                    </td>

                    <td>
                        {
                            escape_html(
                                recommendation.get(
                                    "title"
                                )
                            )
                        }
                    </td>

                    <td>
                        {
                            escape_html(
                                recommendation.get(
                                    "recommended_action"
                                )
                            )
                        }
                    </td>

                    <td>
                        {
                            escape_html(
                                recommendation.get(
                                    "next_step"
                                )
                            )
                        }
                    </td>

                </tr>
                """
            )

        content = f"""
        <div class="table-container">

            <table>

                <thead>

                    <tr>
                        <th>Priority</th>
                        <th>Action Area</th>
                        <th>Recommended Action</th>
                        <th>Next Step</th>
                    </tr>

                </thead>

                <tbody>
                    {''.join(rows)}
                </tbody>

            </table>

        </div>
        """

    return f"""
    <section class="report-section">

        <h2>6. Priority Action Plan</h2>

        <p class="section-description">
            Recommended actions requiring management
            attention before migration approval.
        </p>

        {content}

    </section>
    """


# ============================================================
# MANAGEMENT RECOMMENDATION
# ============================================================

def build_management_recommendation(
    report_data: Dict[str, Any],
) -> str:
    """
    Build final management recommendation.
    """

    summary = report_data[
        "executive_summary"
    ]

    decision = build_decision_message(
        summary
    )

    high_recommendations = summary.get(
        "high_recommendations",
        0,
    )

    critical_recommendations = summary.get(
        "critical_recommendations",
        0,
    )
    readiness_level = summary.get(
        "readiness_level"
    )

    if readiness_level == "READY":

        management_message = (
            "Management may proceed to the next migration "
            "stage while maintaining standard validation "
            "and governance controls."
        )

    elif readiness_level == "READY_WITH_CONDITIONS":

        management_message = (
            "Management should confirm that all defined "
            "conditions and responsibilities are documented "
            "before proceeding to the next migration stage."
        )

    else:

        management_message = (
            "Management should ensure that priority findings "
            "are assigned to responsible owners, corrective "
            "actions are completed, and the assessment is "
            "rerun before final migration approval."
        )
    return f"""
    <section class="management-section">

        <div class="decision-label">
            FINAL MANAGEMENT RECOMMENDATION
        </div>

        <h2>
            {escape_html(decision["decision"])}
        </h2>

        <p>
            Current migration readiness is
            <strong>
                {
                    escape_html(
                        summary.get(
                            "readiness_level"
                        )
                    )
                }
            </strong>
            with a readiness score of
            <strong>
                {
                    format_number(
                        summary.get(
                            "readiness_score"
                        )
                    )
                } / 100
            </strong>.
        </p>

        <p>
            The assessment identified
            <strong>
                {
                    format_number(
                        critical_recommendations
                    )
                }
            </strong>
            critical-priority recommendations and
            <strong>
                {
                    format_number(
                        high_recommendations
                    )
                }
            </strong>
            high-priority recommendations.
        </p>

               <p>
            {escape_html(management_message)}
        </p>
    </section>
    """


# ============================================================
# COMPLETE HTML DOCUMENT
# ============================================================

def build_html_document(
    report_data: Dict[str, Any],
) -> str:
    """
    Build complete executive HTML report.
    """

    generated_at = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )

    body_content = "".join(
    (
        build_report_header(
            report_data,
            generated_at,
        ),
        build_executive_decision(
            report_data
        ),
        build_health_overview(
            report_data
        ),
        build_data_scope(
            report_data
        ),
        build_database_discovery_overview(
            report_data
        ),
        build_business_concerns(
            report_data
        ),
        build_reconciliation_health(
            report_data
        ),
        build_priority_actions(
            report_data
        ),
        build_management_recommendation(
            report_data
        ),
    )
    )

    return f"""
<!DOCTYPE html>
<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>
        Migration Executive Assessment
    </title>

    <style>

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family:
                Arial,
                Helvetica,
                sans-serif;
            background: #f4f6f8;
            color: #1f2933;
            line-height: 1.6;
        }}

        .report-container {{
            max-width: 1250px;
            margin: 0 auto;
            padding: 30px;
        }}

        .report-header {{
            background: #ffffff;
            border: 1px solid #d9e2ec;
            border-radius: 10px;
            padding: 32px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            gap: 30px;
        }}

        .report-label,
        .decision-label {{
            font-size: 12px;
            font-weight: bold;
            letter-spacing: 1.5px;
            color: #616e7c;
        }}

        h1 {{
            margin: 8px 0;
            font-size: 32px;
        }}

        .report-subtitle,
        .section-description {{
            color: #52606d;
        }}

        .report-metadata {{
            min-width: 220px;
        }}

        .report-metadata div {{
            margin-bottom: 15px;
        }}

        .report-metadata strong {{
            display: block;
            font-size: 12px;
            text-transform: uppercase;
            color: #7b8794;
        }}

        .report-metadata span {{
            display: block;
            margin-top: 4px;
        }}

        .decision-section,
        .management-section {{
            background: #ffffff;
            border: 2px solid #9b1c1c;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 24px;
        }}

        .decision-section h2,
        .management-section h2 {{
            margin:
                8px
                0
                12px
                0;
            font-size: 27px;
        }}

        .decision-message {{
            max-width: 850px;
            font-size: 17px;
        }}

        .decision-result {{
            display: inline-block;
            margin-top: 12px;
            padding: 10px 16px;
            border-radius: 5px;
            background: #fde8e8;
            color: #9b1c1c;
            font-weight: bold;
        }}

        .report-section {{
            background: #ffffff;
            border: 1px solid #d9e2ec;
            border-radius: 10px;
            padding: 28px;
            margin-bottom: 24px;
        }}

        .report-section h2 {{
            margin-top: 0;
            margin-bottom: 5px;
            font-size: 23px;
        }}

        .section-description {{
            margin-top: 0;
            margin-bottom: 22px;
        }}

        .metric-grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(210px, 1fr)
                );
            gap: 16px;
        }}

        .metric-card {{
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 20px;
        }}

        .metric-title {{
            font-size: 13px;
            font-weight: bold;
            text-transform: uppercase;
            color: #616e7c;
            margin-bottom: 12px;
        }}

        .metric-number,
        .readiness-score {{
            font-size: 29px;
            font-weight: bold;
        }}

        .readiness-score span {{
            font-size: 15px;
            color: #7b8794;
        }}

        .metric-value {{
            margin-top: 10px;
        }}

        .status-badge {{
            display: inline-block;
            padding: 5px 10px;
            border-radius: 14px;
            font-size: 12px;
            font-weight: bold;
        }}

        .status-success {{
            background: #e6f6ec;
            color: #176b3a;
        }}

        .status-warning {{
            background: #fff7d6;
            color: #8a6116;
        }}

        .status-danger {{
            background: #fde8e8;
            color: #9b1c1c;
        }}

        .status-neutral {{
            background: #edf2f7;
            color: #52606d;
        }}

        .concern-card {{
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 22px;
            margin-bottom: 16px;
        }}

        .concern-header {{
            display: flex;
            justify-content: space-between;
            gap: 20px;
        }}

        .concern-header h3 {{
            margin-top: 0;
        }}

        .concern-block {{
            margin-top: 15px;
        }}

        .concern-block p {{
            margin-top: 5px;
        }}

        .positive-message {{
            padding: 20px;
            border: 1px solid #b7dfc5;
            background: #e6f6ec;
            border-radius: 6px;
        }}

        .table-container {{
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 800px;
        }}

        th {{
            text-align: left;
            background: #f4f6f8;
            padding: 12px;
            border: 1px solid #d9e2ec;
        }}

        td {{
            padding: 12px;
            border: 1px solid #d9e2ec;
            vertical-align: top;
        }}

        @media print {{

            body {{
                background: #ffffff;
            }}

            .report-container {{
                max-width: none;
                padding: 0;
            }}

            .report-section,
            .report-header,
            .decision-section,
            .management-section,
            .concern-card,
            .metric-card {{
                break-inside: avoid;
            }}

        }}

    </style>

</head>

<body>

    <main class="report-container">

        {body_content}

    </main>

</body>

</html>
"""


# ============================================================
# EXECUTIVE REPORT GENERATION
# ============================================================

def generate_executive_report(
    database: str,
) -> Path:
    """
    Generate executive HTML migration report.
    """

    print()
    print("=====================================")
    print("EXECUTIVE REPORT GENERATION STARTED")
    print("=====================================")
    print(f"Database: {database}")
    print()

    report_data = build_report_data(
        database
    )

    html_document = build_html_document(
        report_data
    )

    output_directory = (
        PROJECT_ROOT
        / "reports"
        / "migration"
        / database
    )

    output_file = (
        output_directory
        / "executive_report.html"
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            html_document
        )

    print("=====================================")
    print("EXECUTIVE REPORT GENERATION COMPLETED")
    print("=====================================")
    print(f"Database : {database}")
    print(f"Output   : {output_file}")
    print()

    return output_file


# ============================================================
# COMMAND-LINE ARGUMENTS
# ============================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Generate business-focused migration "
            "executive assessment report."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        choices=SUPPORTED_DATABASES,
        help=(
            "Database whose executive report "
            "should be generated."
        ),
    )

    return parser.parse_args()


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main() -> None:
    """
    Main execution function.
    """

    arguments = parse_arguments()

    try:

        generate_executive_report(
            arguments.database
        )

    except Exception as error:

        print()
        print("=====================================")
        print("EXECUTIVE REPORT GENERATION FAILED")
        print("=====================================")
        print(f"Error: {error}")
        print()

        sys.exit(1)


if __name__ == "__main__":
    main()