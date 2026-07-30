"""
Migration Technical Report Generator.

Generates a detailed HTML report for technical stakeholders
using the common migration report data model.

The report includes:
    - Assessment summary
    - Source profiling summary
    - Dataset-level profiling metrics
    - Profiling findings
    - Reconciliation summary
    - Dataset-level reconciliation results
    - Risk assessment
    - Complexity assessment
    - Readiness assessment
    - Detailed recommendations

Generates:
    reports/migration/<database>/technical_report.html
"""

import argparse
import html
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


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

def escape_html(
    value: Any,
) -> str:
    """
    Convert a value into HTML-safe text.
    """

    if value is None:
        return "-"

    return html.escape(
        str(value)
    )


def format_number(
    value: Any,
) -> str:
    """
    Format numeric values for technical readability.
    """

    if value is None:
        return "-"

    try:
        return f"{int(value):,}"

    except (
        TypeError,
        ValueError,
    ):
        return escape_html(value)


def format_percentage(
    value: Any,
) -> str:
    """
    Format percentage values.
    """

    if value is None:
        return "-"

    try:
        return f"{float(value):.2f}%"

    except (
        TypeError,
        ValueError,
    ):
        return escape_html(value)


def format_bytes(
    value: Any,
) -> str:
    """
    Convert bytes into a readable file-size representation.
    """

    if value is None:
        return "-"

    try:
        size = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return escape_html(value)

    units = (
        "B",
        "KB",
        "MB",
        "GB",
        "TB",
    )

    unit_index = 0

    while (
        size >= 1024
        and unit_index < len(units) - 1
    ):

        size /= 1024

        unit_index += 1

    return (
        f"{size:.2f} "
        f"{units[unit_index]}"
    )


def get_status_class(
    value: Any,
) -> str:
    """
    Return CSS class for status, severity, or assessment level.
    """

    normalized_value = str(
        value or ""
    ).upper()

    success_values = {
        "READY",
        "RECONCILED",
        "MATCHED",
        "READY_FOR_NEXT_STAGE",
        "LOW",
    }

    warning_values = {
        "MEDIUM",
        "READY_WITH_CONDITIONS",
        "CONDITIONAL_APPROVAL",
    }

    danger_values = {
        "HIGH",
        "CRITICAL",
        "NOT_READY",
        "NEEDS_REMEDIATION",
        "NOT_RECONCILED",
        "MISMATCHED",
        "ACTION_REQUIRED",
        "REMEDIATION_REQUIRED",
        "VERY_HIGH",
    }

    if normalized_value in success_values:
        return "status-success"

    if normalized_value in warning_values:
        return "status-warning"

    if normalized_value in danger_values:
        return "status-danger"

    return "status-neutral"


def render_status_badge(
    value: Any,
) -> str:
    """
    Render a status value as an HTML badge.
    """

    return (
        f'<span class="status-badge '
        f'{get_status_class(value)}">'
        f'{escape_html(value)}'
        f'</span>'
    )


def render_empty_message(
    message: str,
) -> str:
    """
    Render a standardized empty-state message.
    """

    return (
        '<div class="empty-message">'
        f'{escape_html(message)}'
        '</div>'
    )


# ============================================================
# REPORT HEADER
# ============================================================

def build_report_header(
    report_data: Dict[str, Any],
    generated_at: str,
) -> str:
    """
    Build technical report header.
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
                Migration Technical Assessment Report
            </h1>

            <p class="report-subtitle">
                Detailed technical analysis of profiling,
                reconciliation, assessment, and migration
                recommendations.
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
# ASSESSMENT OVERVIEW
# ============================================================

def build_assessment_overview(
    report_data: Dict[str, Any],
) -> str:
    """
    Build top-level technical assessment overview.
    """

    summary = report_data[
        "executive_summary"
    ]

    return f"""
    <section class="report-section">
        <h2>1. Assessment Overview</h2>

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
                    Risk Level
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
                    Complexity Level
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

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "readiness_score"
                            )
                        )
                    }
                </div>

                <div class="metric-detail">
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
# PROFILING SUMMARY
# ============================================================

def build_profiling_summary(
    report_data: Dict[str, Any],
) -> str:
    """
    Build profiling summary section.
    """

    summary = report_data[
        "profiling"
    ][
        "summary"
    ]

    return f"""
    <section class="report-section">
        <h2>2. Source Data Profiling Summary</h2>

        <div class="metric-grid">

            <div class="metric-card">
                <div class="metric-title">
                    Source Files
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "total_files_found"
                            )
                        )
                    }
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-title">
                    Total Records
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "total_rows"
                            )
                        )
                    }
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-title">
                    Total Columns
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "total_columns"
                            )
                        )
                    }
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-title">
                    Profiling Issues
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "total_profiling_issues"
                            )
                        )
                    }
                </div>
            </div>

        </div>

        <div class="severity-grid">

            <div class="severity-card">
                <strong>High Severity</strong>
                <span>
                    {
                        format_number(
                            summary.get(
                                "high_severity_issues"
                            )
                        )
                    }
                </span>
            </div>

            <div class="severity-card">
                <strong>Medium Severity</strong>
                <span>
                    {
                        format_number(
                            summary.get(
                                "medium_severity_issues"
                            )
                        )
                    }
                </span>
            </div>

            <div class="severity-card">
                <strong>Low Severity</strong>
                <span>
                    {
                        format_number(
                            summary.get(
                                "low_severity_issues"
                            )
                        )
                    }
                </span>
            </div>

        </div>
    </section>
    """


# ============================================================
# DATASET PROFILING TABLE
# ============================================================

def build_dataset_profiling_table(
    report_data: Dict[str, Any],
) -> str:
    """
    Build dataset-level profiling table.
    """

    datasets = report_data[
        "profiling"
    ][
        "datasets"
    ]

    if not datasets:

        table_content = render_empty_message(
            "No profiling datasets are available."
        )

    else:

        rows = []

        for dataset in datasets:

            rows.append(
                f"""
                <tr>
                    <td>
                        {
                            escape_html(
                                dataset.get(
                                    "file_name"
                                )
                            )
                        }
                    </td>

                    <td>
                        {
                            escape_html(
                                dataset.get(
                                    "file_type"
                                )
                            )
                        }
                    </td>

                    <td class="number-cell">
                        {
                            format_number(
                                dataset.get(
                                    "total_rows"
                                )
                            )
                        }
                    </td>

                    <td class="number-cell">
                        {
                            format_number(
                                dataset.get(
                                    "total_columns"
                                )
                            )
                        }
                    </td>

                    <td class="number-cell">
                        {
                            format_number(
                                dataset.get(
                                    "duplicate_rows"
                                )
                            )
                        }
                    </td>

                    <td class="number-cell">
                        {
                            format_number(
                                dataset.get(
                                    "total_null_cells"
                                )
                            )
                        }
                    </td>

                    <td class="number-cell">
                        {
                            format_number(
                                dataset.get(
                                    "total_issues"
                                )
                            )
                        }
                    </td>

                    <td>
                        {
                            format_bytes(
                                dataset.get(
                                    "file_size_bytes"
                                )
                            )
                        }
                    </td>
                </tr>
                """
            )

        table_content = f"""
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Source File</th>
                        <th>Type</th>
                        <th>Rows</th>
                        <th>Columns</th>
                        <th>Duplicates</th>
                        <th>Null Cells</th>
                        <th>Issues</th>
                        <th>File Size</th>
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
        <h2>3. Dataset Profiling Details</h2>

        {table_content}
    </section>
    """


# ============================================================
# PROFILING FINDINGS
# ============================================================

def build_profiling_findings(
    report_data: Dict[str, Any],
) -> str:
    """
    Build detailed profiling findings section.
    """

    datasets = report_data[
        "profiling"
    ][
        "datasets"
    ]

    findings = []

    for dataset in datasets:

        file_name = dataset.get(
            "file_name"
        )

        for issue in dataset.get(
            "issues",
            [],
        ):

            findings.append(
                {
                    "dataset": file_name,
                    "issue_type": issue.get(
                        "issue_type"
                    ),
                    "severity": issue.get(
                        "severity"
                    ),
                    "column": issue.get(
                        "column"
                    ),
                    "message": issue.get(
                        "message"
                    ),
                }
            )

    if not findings:

        content = render_empty_message(
            "No profiling findings were detected."
        )

    else:

        rows = []

        for finding in findings:

            rows.append(
                f"""
                <tr>
                    <td>
                        {
                            escape_html(
                                finding["dataset"]
                            )
                        }
                    </td>

                    <td>
                        {
                            escape_html(
                                finding["issue_type"]
                            )
                        }
                    </td>

                    <td>
                        {
                            render_status_badge(
                                finding["severity"]
                            )
                        }
                    </td>

                    <td>
                        {
                            escape_html(
                                finding["column"]
                            )
                        }
                    </td>

                    <td>
                        {
                            escape_html(
                                finding["message"]
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
                        <th>Dataset</th>
                        <th>Issue Type</th>
                        <th>Severity</th>
                        <th>Column</th>
                        <th>Technical Finding</th>
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
        <h2>4. Profiling Findings</h2>

        {content}
    </section>
    """


# ============================================================
# RECONCILIATION SUMMARY
# ============================================================

def build_reconciliation_summary(
    report_data: Dict[str, Any],
) -> str:
    """
    Build reconciliation summary.
    """

    summary = report_data[
        "reconciliation"
    ][
        "summary"
    ]

    return f"""
    <section class="report-section">
        <h2>5. Reconciliation Summary</h2>

        <div class="metric-grid">

            <div class="metric-card">
                <div class="metric-title">
                    Expected Datasets
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "expected_datasets"
                            )
                        )
                    }
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-title">
                    Reconciled
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
                    Total Issues
                </div>

                <div class="metric-number">
                    {
                        format_number(
                            summary.get(
                                "total_issues"
                            )
                        )
                    }
                </div>
            </div>

        </div>
    </section>
    """


# ============================================================
# RECONCILIATION DETAILS
# ============================================================

def build_reconciliation_details(
    report_data: Dict[str, Any],
) -> str:
    """
    Build dataset-level reconciliation details.
    """

    datasets = report_data[
        "reconciliation"
    ][
        "datasets"
    ]

    if not datasets:

        content = render_empty_message(
            "No reconciliation datasets are available."
        )

    else:

        rows = []

        for dataset in datasets:

            rows.append(
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
                            escape_html(
                                dataset.get(
                                    "target_name"
                                )
                            )
                        }
                    </td>

                    <td class="number-cell">
                        {
                            format_number(
                                dataset.get(
                                    "expected_rows"
                                )
                            )
                        }
                    </td>

                    <td class="number-cell">
                        {
                            format_number(
                                dataset.get(
                                    "actual_rows"
                                )
                            )
                        }
                    </td>

                    <td class="number-cell">
                        {
                            format_number(
                                dataset.get(
                                    "row_difference"
                                )
                            )
                        }
                    </td>

                    <td>
                        {
                            format_percentage(
                                dataset.get(
                                    "row_match_percentage"
                                )
                            )
                        }
                    </td>

                    <td class="number-cell">
                        {
                            format_number(
                                dataset.get(
                                    "expected_columns"
                                )
                            )
                        }
                    </td>

                    <td class="number-cell">
                        {
                            format_number(
                                dataset.get(
                                    "actual_columns"
                                )
                            )
                        }
                    </td>

                    <td>
                        {
                            render_status_badge(
                                dataset.get(
                                    "status"
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
                        <th>Dataset</th>
                        <th>Target Object</th>
                        <th>Expected Rows</th>
                        <th>Actual Rows</th>
                        <th>Difference</th>
                        <th>Row Match</th>
                        <th>Expected Columns</th>
                        <th>Actual Columns</th>
                        <th>Status</th>
                    </tr>
                </thead>

                <tbody>
                    {''.join(rows)}
                </tbody>
            </table>
        </div>
        """

    extra_targets = report_data[
        "reconciliation"
    ].get(
        "extra_target_datasets",
        [],
    )

    if extra_targets:

        extra_target_content = (
            '<div class="technical-note">'
            '<strong>Extra Target Datasets:</strong> '
            + ", ".join(
                escape_html(target)
                for target in extra_targets
            )
            + "</div>"
        )

    else:

        extra_target_content = ""

    return f"""
    <section class="report-section">
        <h2>6. Dataset Reconciliation Details</h2>

        {content}

        {extra_target_content}
    </section>
    """
# ============================================================
# DATABASE DISCOVERY
# ============================================================

def build_database_discovery(
    report_data: Dict[str, Any],
) -> str:
    """
    Build database discovery, growth, retention, and SLA section.
    """

    discovery = report_data.get(
        "discovery",
        {},
    )

    summary = discovery.get(
        "summary",
        {},
    )

    datasets = discovery.get(
        "datasets",
        [],
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

    dataset_rows = []

    for dataset in datasets:

        dataset_rows.append(
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
                        escape_html(
                            dataset.get(
                                "dataset_type"
                            )
                        )
                    }
                </td>

                <td class="number-cell">
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

    if dataset_rows:

        dataset_content = f"""
        <div class="table-container">

            <table>

                <thead>
                    <tr>
                        <th>Database Dataset</th>
                        <th>Type</th>
                        <th>Record Count</th>
                    </tr>
                </thead>

                <tbody>
                    {''.join(dataset_rows)}
                </tbody>

            </table>

        </div>
        """

    else:

        dataset_content = render_empty_message(
            "No database discovery datasets are available."
        )

    return f"""
    <section class="report-section">

        <h2>7. Database Discovery Analysis</h2>

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
                        format_percentage(
                            growth_summary.get(
                                "overall_growth_rate_percent"
                            )
                        )
                    }
                </div>
            </div>

        </div>

        <div class="severity-grid">

            <div class="severity-card">
                <strong>Required Retention</strong>

                <span>
                    {
                        format_number(
                            retention.get(
                                "required_retention_days"
                            )
                        )
                    }
                    days
                </span>
            </div>

            <div class="severity-card">
                <strong>Archive Required</strong>

                <span>
                    {
                        escape_html(
                            retention.get(
                                "archive_required"
                            )
                        )
                    }
                </span>
            </div>

            <div class="severity-card">
                <strong>Maximum Migration Time</strong>

                <span>
                    {
                        format_number(
                            sla.get(
                                "maximum_migration_duration_minutes"
                            )
                        )
                    }
                    minutes
                </span>
            </div>

            <div class="severity-card">
                <strong>Maximum Downtime</strong>

                <span>
                    {
                        format_number(
                            sla.get(
                                "maximum_downtime_minutes"
                            )
                        )
                    }
                    minutes
                </span>
            </div>

        </div>

        <h3>Discovered Database Datasets</h3>

        {dataset_content}

    </section>
    """

# ============================================================
# ASSESSMENT BREAKDOWN
# ============================================================

def build_assessment_breakdown(
    report_data: Dict[str, Any],
) -> str:
    """
    Build detailed risk, complexity, and readiness assessment.
    """

    assessment = report_data[
        "assessment"
    ]

    risk = assessment[
        "risk"
    ]

    complexity = assessment[
        "complexity"
    ]

    readiness = assessment[
        "readiness"
    ]

    return f"""
    <section class="report-section">
        <h2>8. Migration Assessment Breakdown</h2>

        <div class="assessment-grid">

            <div class="assessment-card">
                <h3>Migration Risk</h3>

                <div class="assessment-score">
                    {
                        format_number(
                            risk.get(
                                "risk_score"
                            )
                        )
                    }
                </div>

                <div>
                    {
                        render_status_badge(
                            risk.get(
                                "risk_level"
                            )
                        )
                    }
                </div>

                <hr>

                <p>
                    Profiling Risk Score:
                    <strong>
                        {
                            format_number(
                                risk.get(
                                    "risk_score_breakdown",
                                    {},
                                ).get(
                                    "profiling_risk_score"
                                )
                            )
                        }
                    </strong>
                </p>

                <p>
                    Reconciliation Risk Score:
                    <strong>
                        {
                            format_number(
                                risk.get(
                                    "risk_score_breakdown",
                                    {},
                                ).get(
                                    "reconciliation_risk_score"
                                )
                            )
                        }
                    </strong>
                </p>
                <p>
                    Discovery Risk Score:
                    <strong>
                        {
                            format_number(
                                risk.get(
                                    "risk_score_breakdown",
                                    {},
                                ).get(
                                    "discovery_risk_score"
                                )
                            )
                        }
                    </strong>
                </p>

                <p>
                    Growth Risk Score:
                    <strong>
                        {
                            format_number(
                                risk.get(
                                    "risk_score_breakdown",
                                    {},
                                ).get(
                                    "growth_risk_score"
                                )
                            )
                        }
                    </strong>
                </p>

                <p>
                    Retention Risk Score:
                    <strong>
                        {
                            format_number(
                                risk.get(
                                    "risk_score_breakdown",
                                    {},
                                ).get(
                                    "retention_risk_score"
                                )
                            )
                        }
                    </strong>
                </p>

                <p>
                    SLA Risk Score:
                    <strong>
                        {
                            format_number(
                                risk.get(
                                    "risk_score_breakdown",
                                    {},
                                ).get(
                                    "sla_risk_score"
                                )
                            )
                        }
                    </strong>
                </p>
            </div>

            <div class="assessment-card">
                <h3>Migration Complexity</h3>

                <div class="assessment-score">
                    {
                        format_number(
                            complexity.get(
                                "complexity_score"
                            )
                        )
                    }
                </div>

                <div>
                    {
                        render_status_badge(
                            complexity.get(
                                "complexity_level"
                            )
                        )
                    }
                </div>

                <hr>

                <p>
                    Data Volume Score:
                    <strong>
                        {
                            format_number(
                                complexity.get(
                                    "complexity_score_breakdown",
                                    {},
                                ).get(
                                    "data_volume_score"
                                )
                            )
                        }
                    </strong>
                </p>

                <p>
                    Dataset Count Score:
                    <strong>
                        {
                            format_number(
                                complexity.get(
                                    "complexity_score_breakdown",
                                    {},
                                ).get(
                                    "dataset_count_score"
                                )
                            )
                        }
                    </strong>
                </p>

                <p>
                    Schema Width Score:
                    <strong>
                        {
                            format_number(
                                complexity.get(
                                    "complexity_score_breakdown",
                                    {},
                                ).get(
                                    "schema_width_score"
                                )
                            )
                        }
                    </strong>
                </p>

                <p>
                    Reconciliation Score:
                    <strong>
                        {
                            format_number(
                                complexity.get(
                                    "complexity_score_breakdown",
                                    {},
                                ).get(
                                    "reconciliation_score"
                                )
                            )
                        }
                    </strong>
                </p>
                
                <p>
                    Growth Score:
                    <strong>
                        {
                            format_number(
                                complexity.get(
                                    "complexity_score_breakdown",
                                    {},
                                ).get(
                                    "growth_score"
                                )
                            )
                        }
                    </strong>
                </p>
                            </div>

            <div class="assessment-card">
                <h3>Migration Readiness</h3>

                <div class="assessment-score">
                    {
                        format_number(
                            readiness.get(
                                "readiness_score"
                            )
                        )
                    }
                </div>

                <div>
                    {
                        render_status_badge(
                            readiness.get(
                                "readiness_level"
                            )
                        )
                    }
                </div>

                <hr>

                <p>
                    Profiling Penalty:
                    <strong>
                        {
                            format_number(
                                readiness.get(
                                    "readiness_score_breakdown",
                                    {},
                                ).get(
                                    "profiling_penalty"
                                )
                            )
                        }
                    </strong>
                </p>

                <p>
                    Reconciliation Penalty:
                    <strong>
                        {
                            format_number(
                                readiness.get(
                                    "readiness_score_breakdown",
                                    {},
                                ).get(
                                    "reconciliation_penalty"
                                )
                            )
                        }
                    </strong>
                </p>

                <p>
                    Risk Penalty:
                    <strong>
                        {
                            format_number(
                                readiness.get(
                                    "readiness_score_breakdown",
                                    {},
                                ).get(
                                    "risk_penalty"
                                )
                            )
                        }
                    </strong>
                </p>

                <p>
                    Complexity Penalty:
                    <strong>
                        {
                            format_number(
                                readiness.get(
                                    "readiness_score_breakdown",
                                    {},
                                ).get(
                                    "complexity_penalty"
                                )
                            )
                        }
                    </strong>
                </p>
                
                <p>
                    Retention Penalty:
                    <strong>
                        {
                            format_number(
                                readiness.get(
                                    "readiness_score_breakdown",
                                    {},
                                ).get(
                                    "retention_penalty"
                                )
                            )
                        }
                    </strong>
                </p>

                <p>
                    SLA Penalty:
                    <strong>
                        {
                            format_number(
                                readiness.get(
                                    "readiness_score_breakdown",
                                    {},
                                ).get(
                                    "sla_penalty"
                                )
                            )
                        }
                    </strong>
                </p>
            </div>

        </div>
    </section>
    """


# ============================================================
# TECHNICAL RECOMMENDATIONS
# ============================================================

def build_recommendations(
    report_data: Dict[str, Any],
) -> str:
    """
    Build detailed recommendation section.
    """

    recommendations = report_data[
        "recommendation"
    ][
        "recommendations"
    ]

    if not recommendations:

        content = render_empty_message(
            "No migration recommendations were generated."
        )

    else:

        recommendation_cards = []

        for recommendation in recommendations:

            recommendation_cards.append(
                f"""
                <div class="recommendation-card">

                    <div class="recommendation-header">

                        <div>
                            <span class="recommendation-id">
                                {
                                    escape_html(
                                        recommendation.get(
                                            "recommendation_id"
                                        )
                                    )
                                }
                            </span>

                            <h3>
                                {
                                    escape_html(
                                        recommendation.get(
                                            "title"
                                        )
                                    )
                                }
                            </h3>
                        </div>

                        {
                            render_status_badge(
                                recommendation.get(
                                    "priority"
                                )
                            )
                        }

                    </div>

                    <div class="recommendation-meta">
                        <span>
                            <strong>Category:</strong>
                            {
                                escape_html(
                                    recommendation.get(
                                        "category"
                                    )
                                )
                            }
                        </span>

                        <span>
                            <strong>Source:</strong>
                            {
                                escape_html(
                                    recommendation.get(
                                        "source"
                                    )
                                )
                            }
                        </span>

                        <span>
                            <strong>Dataset:</strong>
                            {
                                escape_html(
                                    recommendation.get(
                                        "dataset"
                                    )
                                )
                            }
                        </span>

                        <span>
                            <strong>Column:</strong>
                            {
                                escape_html(
                                    recommendation.get(
                                        "column"
                                    )
                                )
                            }
                        </span>
                    </div>

                    <div class="recommendation-content">

                        <div>
                            <strong>Finding</strong>

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

                        <div>
                            <strong>Business Impact</strong>

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

                        <div>
                            <strong>Recommended Action</strong>

                            <p>
                                {
                                    escape_html(
                                        recommendation.get(
                                            "recommended_action"
                                        )
                                    )
                                }
                            </p>
                        </div>

                        <div>
                            <strong>Next Step</strong>

                            <p>
                                {
                                    escape_html(
                                        recommendation.get(
                                            "next_step"
                                        )
                                    )
                                }
                            </p>
                        </div>

                    </div>

                </div>
                """
            )

        content = "".join(
            recommendation_cards
        )

    return f"""
    <section class="report-section">
        <h2>9. Detailed Migration Recommendations</h2>

        {content}
    </section>
    """


# ============================================================
# HTML DOCUMENT
# ============================================================

def build_html_document(
    report_data: Dict[str, Any],
) -> str:
    """
    Build complete technical HTML report.
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
            build_assessment_overview(
                report_data
            ),
            build_profiling_summary(
                report_data
            ),
            build_dataset_profiling_table(
                report_data
            ),
            build_profiling_findings(
                report_data
            ),
            build_reconciliation_summary(
                report_data
            ),
            build_reconciliation_details(
                report_data
            ),
            build_database_discovery(
                report_data
            ),
            build_assessment_breakdown(
                report_data
            ),
            build_recommendations(
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
        Migration Technical Assessment Report
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
            max-width: 1500px;
            margin: 0 auto;
            padding: 30px;
        }}

        .report-header {{
            background: #ffffff;
            border-radius: 10px;
            padding: 32px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            gap: 30px;
            border: 1px solid #d9e2ec;
        }}

        .report-label {{
            font-size: 13px;
            font-weight: bold;
            letter-spacing: 1.5px;
            margin-bottom: 8px;
        }}

        h1 {{
            margin: 0;
            font-size: 32px;
        }}

        .report-subtitle {{
            max-width: 800px;
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

        .report-section {{
            background: #ffffff;
            border: 1px solid #d9e2ec;
            border-radius: 10px;
            padding: 28px;
            margin-bottom: 24px;
        }}

        .report-section h2 {{
            margin-top: 0;
            margin-bottom: 22px;
            font-size: 23px;
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

        .metric-number {{
            font-size: 28px;
            font-weight: bold;
        }}

        .metric-detail {{
            margin-top: 10px;
        }}

        .severity-grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(200px, 1fr)
                );
            gap: 16px;
            margin-top: 20px;
        }}

        .severity-card {{
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 18px;
            display: flex;
            justify-content: space-between;
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

        .table-container {{
            width: 100%;
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            min-width: 850px;
        }}

        th {{
            text-align: left;
            background: #f4f6f8;
            padding: 12px;
            border: 1px solid #d9e2ec;
            font-size: 13px;
        }}

        td {{
            padding: 12px;
            border: 1px solid #d9e2ec;
            vertical-align: top;
        }}

        .number-cell {{
            text-align: right;
        }}

        .assessment-grid {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(280px, 1fr)
                );
            gap: 20px;
        }}

        .assessment-card {{
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 22px;
        }}

        .assessment-card h3 {{
            margin-top: 0;
        }}

        .assessment-score {{
            font-size: 36px;
            font-weight: bold;
            margin-bottom: 8px;
        }}

        .assessment-card hr {{
            border: 0;
            border-top: 1px solid #d9e2ec;
            margin: 20px 0;
        }}

        .recommendation-card {{
            border: 1px solid #d9e2ec;
            border-radius: 8px;
            padding: 22px;
            margin-bottom: 18px;
        }}

        .recommendation-header {{
            display: flex;
            justify-content: space-between;
            gap: 20px;
            align-items: flex-start;
        }}

        .recommendation-header h3 {{
            margin:
                5px
                0
                0
                0;
        }}

        .recommendation-id {{
            font-size: 12px;
            font-weight: bold;
            color: #616e7c;
        }}

        .recommendation-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 16px;
            margin: 18px 0;
            font-size: 13px;
        }}

        .recommendation-content {{
            display: grid;
            grid-template-columns:
                repeat(
                    auto-fit,
                    minmax(250px, 1fr)
                );
            gap: 18px;
        }}

        .recommendation-content p {{
            margin-bottom: 0;
        }}

        .technical-note {{
            margin-top: 18px;
            padding: 15px;
            background: #f4f6f8;
            border-radius: 6px;
        }}

        .empty-message {{
            padding: 20px;
            border: 1px dashed #bcccdc;
            border-radius: 6px;
            color: #616e7c;
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
            .recommendation-card,
            .assessment-card,
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
# TECHNICAL REPORT GENERATION
# ============================================================

def generate_technical_report(
    database: str,
) -> Path:
    """
    Generate technical HTML migration report.
    """

    print()
    print("=====================================")
    print("TECHNICAL REPORT GENERATION STARTED")
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
        / "technical_report.html"
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
    print("TECHNICAL REPORT GENERATION COMPLETED")
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
            "Generate detailed migration "
            "technical assessment report."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        choices=SUPPORTED_DATABASES,
        help=(
            "Database whose technical report "
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

        generate_technical_report(
            arguments.database
        )

    except Exception as error:

        print()
        print("=====================================")
        print("TECHNICAL REPORT GENERATION FAILED")
        print("=====================================")
        print(f"Error: {error}")
        print()

        sys.exit(1)


if __name__ == "__main__":
    main()