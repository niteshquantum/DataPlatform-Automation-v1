"""
Migration Report Data Builder.

Loads and consolidates migration analysis outputs into a common
report model shared by Technical and Executive report generators.

Current inputs:
    - Profiling
    - Reconciliation
    - Assessment
    - Recommendation

Discovery findings can be integrated later without changing the
Technical and Executive report input architecture.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ============================================================
# CONSTANTS
# ============================================================

SUPPORTED_DATABASES = (
    "mysql",
    "postgresql",
    "mssql",
    "mongodb",
)


# ============================================================
# JSON FILE LOADER
# ============================================================

def load_json_file(
    file_path: Path,
    input_name: str,
) -> Dict[str, Any]:
    """
    Load a required JSON input file.
    """

    if not file_path.exists():

        raise FileNotFoundError(
            f"{input_name} not found: {file_path}"
        )

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ============================================================
# REPORT INPUT PATHS
# ============================================================

def get_report_input_paths(
    database: str,
) -> Dict[str, Path]:
    """
    Return all required report input paths.
    """

    return {
        "profiling": (
            PROJECT_ROOT
            / "metadata"
            / "profiling"
            / database
            / "profiling.json"
        ),
        "reconciliation": (
            PROJECT_ROOT
            / "metadata"
            / "reconciliation"
            / database
            / "reconciliation.json"
        ),
        "assessment": (
            PROJECT_ROOT
            / "metadata"
            / "assessment"
            / database
            / "assessment.json"
        ),
        "recommendation": (
            PROJECT_ROOT
            / "metadata"
            / "recommendation"
            / database
            / "recommendation.json"
        ),
        "discovery": (
            PROJECT_ROOT
            / "metadata"
            / "discovery"
            / database
            / "discovery.json"
        ),
        "growth": (
            PROJECT_ROOT
            / "metadata"
            / "discovery"
            / database
            / "growth_analysis.json"
        ),
        "requirements": (
            PROJECT_ROOT
            / "metadata"
            / "discovery"
            / database
            / "requirements_analysis.json"
        ),
    }


# ============================================================
# INPUT LOADING
# ============================================================

def load_report_inputs(
    database: str,
) -> Dict[str, Dict[str, Any]]:
    """
    Load all migration report inputs.
    """

    input_paths = get_report_input_paths(
        database
    )

    loaded = {}

    for input_name, file_path in input_paths.items():

        loaded[input_name] = (
            load_json_file(
                file_path,
                input_name,
            )
        )

    return loaded


# ============================================================
# INPUT VALIDATION
# ============================================================

def _get_metadata_timestamp(
    output: Dict[str, Any],
    metadata_key: str,
) -> Optional[str]:

    metadata = output.get(metadata_key, {})

    return metadata.get("generated_at") or metadata.get("generated_at_utc")


def _get_metadata_database(
    output: Dict[str, Any],
    metadata_key: str,
) -> Optional[str]:

    metadata = output.get(metadata_key, {})

    return metadata.get("database")


def _get_metadata_build_number(
    output: Dict[str, Any],
    metadata_key: str,
) -> Optional[str]:

    metadata = output.get(metadata_key, {})

    return metadata.get("pipeline_build_number")


def validate_artifact_freshness(
    database: str,
    report_inputs: Dict[str, Dict[str, Any]],
    current_build_number: Optional[str] = None,
) -> None:
    """
    Validate that all input artifacts are mutually compatible
    and belong to the current pipeline run.

    Supported provenance modes:
        VERIFIED            — all artifacts share the same pipeline
                              build number and database identity
        UNVERIFIED_LEGACY   — one or more artifacts lack provenance
                              metadata; accepted with warning
        MISMATCHED          — artifacts belong to different databases
                              or runs; rejected
        STALE               — artifact build number indicates a
                              previous run; rejected

    Older JSON artifacts without provenance metadata are accepted
    as UNVERIFIED_LEGACY and do not cause report generation to fail.
    """

    validation_rules = {
        "profiling": "profiling_metadata",
        "reconciliation": "reconciliation_metadata",
        "assessment": "assessment_metadata",
        "recommendation": "recommendation_metadata",
    }

    databases = []
    build_numbers = []
    unverified_count = 0

    for input_name, metadata_key in validation_rules.items():

        output = report_inputs[input_name]

        if metadata_key not in output:

            raise ValueError(
                f"{metadata_key} is missing "
                f"from {input_name} output."
            )

        artifact_database = _get_metadata_database(
            output,
            metadata_key,
        )

        if artifact_database is None:

            unverified_count += 1

        elif artifact_database != database:

            raise ValueError(
                f"{input_name} output database "
                f"does not match selected database "
                f"'{database}'. "
                f"Artifact reports '{artifact_database}'. "
                f"Possible cross-database contamination."
            )

        else:

            databases.append(artifact_database)

        artifact_build_number = _get_metadata_build_number(
            output,
            metadata_key,
        )

        if artifact_build_number is not None:

            build_numbers.append(artifact_build_number)

        else:

            unverified_count += 1

    if len(set(databases)) > 1:

        raise ValueError(
            "Input artifacts belong to different databases. "
            f"Found databases: {sorted(set(databases))}. "
            "Reports cannot mix cross-database artifacts."
        )

    all_tagged = len(build_numbers) == len(validation_rules)
    none_tagged = len(build_numbers) == 0

    if none_tagged:

        return

    if not all_tagged:

        raise ValueError(
            "Input artifacts have mixed run-identity metadata. "
            f"Tagged artifacts: {len(build_numbers)}, "
            f"untagged artifacts: {len(validation_rules) - len(build_numbers)}. "
            "Reports cannot mix tagged and untagged artifacts."
        )

    if len(set(build_numbers)) > 1:

        raise ValueError(
            "Input artifacts belong to different pipeline runs. "
            f"Found build numbers: {sorted(set(build_numbers))}. "
            "Reports cannot mix artifacts from different builds."
        )

    if current_build_number is not None and build_numbers[0] != current_build_number:

        raise ValueError(
            "Input artifacts belong to a previous pipeline run. "
            f"Artifact build number: {build_numbers[0]}. "
            f"Current build number: {current_build_number}. "
            "Stale artifacts are not allowed."
        )


def validate_report_inputs(
    database: str,
    report_inputs: Dict[str, Dict[str, Any]],
    current_build_number: Optional[str] = None,
) -> None:
    """
    Validate required structures, ensure all inputs belong
    to the selected database, and verify artifact freshness.
    """

    validation_rules = {
        "profiling": {
            "metadata": "profiling_metadata",
            "summary": "profiling_summary",
        },
        "reconciliation": {
            "metadata": "reconciliation_metadata",
            "summary": "reconciliation_summary",
        },
        "assessment": {
            "metadata": "assessment_metadata",
            "summary": "assessment_summary",
        },
        "recommendation": {
            "metadata": "recommendation_metadata",
            "summary": "recommendation_summary",
        },
    }

    for input_name, rules in validation_rules.items():

        output = report_inputs[input_name]

        metadata_key = rules["metadata"]

        summary_key = rules["summary"]

        if metadata_key not in output:

            raise ValueError(
                f"{metadata_key} is missing "
                f"from {input_name} output."
            )

        if summary_key not in output:

            raise ValueError(
                f"{summary_key} is missing "
                f"from {input_name} output."
            )

        input_database = output[
            metadata_key
        ].get("database")

        if input_database != database:

            raise ValueError(
                f"{input_name} output database "
                f"does not match selected database "
                f"'{database}'."
            )

    validate_artifact_freshness(
        database,
        report_inputs,
        current_build_number,
    )


# ============================================================
# PROFILING REPORT MODEL
# ============================================================

def build_profiling_report_model(
    profiling_output: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build report-friendly profiling information.
    """

    summary = profiling_output[
        "profiling_summary"
    ]

    datasets = []

    for dataset in profiling_output.get(
        "datasets",
        [],
    ):

        datasets.append(
            {
                "file_name": dataset.get(
                    "file_name"
                ),
                "file_type": dataset.get(
                    "file_type"
                ),
                "file_size_bytes": dataset.get(
                    "file_size_bytes",
                    0,
                ),
                "total_rows": dataset.get(
                    "basic_metrics",
                    {},
                ).get(
                    "total_rows",
                    0,
                ),
                "total_columns": dataset.get(
                    "basic_metrics",
                    {},
                ).get(
                    "total_columns",
                    0,
                ),
                "duplicate_rows": dataset.get(
                    "basic_metrics",
                    {},
                ).get(
                    "duplicate_rows",
                    0,
                ),
                "total_null_cells": dataset.get(
                    "data_quality_summary",
                    {},
                ).get(
                    "total_null_cells",
                    0,
                ),
                "total_issues": dataset.get(
                    "profiling_issue_summary",
                    {},
                ).get(
                    "total_issues",
                    0,
                ),
                "high_severity_issues": dataset.get(
                    "profiling_issue_summary",
                    {},
                ).get(
                    "high_severity_issues",
                    0,
                ),
                "medium_severity_issues": dataset.get(
                    "profiling_issue_summary",
                    {},
                ).get(
                    "medium_severity_issues",
                    0,
                ),
                "low_severity_issues": dataset.get(
                    "profiling_issue_summary",
                    {},
                ).get(
                    "low_severity_issues",
                    0,
                ),
                "issues": dataset.get(
                    "profiling_issues",
                    [],
                ),
            }
        )

    return {
        "summary": summary,
        "datasets": datasets,
    }


# ============================================================
# RECONCILIATION REPORT MODEL
# ============================================================

def build_reconciliation_report_model(
    reconciliation_output: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build report-friendly reconciliation information.
    """

    summary = reconciliation_output[
        "reconciliation_summary"
    ]

    datasets = []

    for dataset in reconciliation_output.get(
        "datasets",
        [],
    ):

        row_reconciliation = dataset.get(
            "row_reconciliation",
            {},
        )

        column_reconciliation = dataset.get(
            "column_reconciliation",
            {},
        )

        datasets.append(
            {
                "dataset_name": dataset.get(
                    "dataset_name"
                ),
                "source_file": dataset.get(
                    "source_file"
                ),
                "target_name": dataset.get(
                    "target_name"
                ),
                "status": dataset.get(
                    "reconciliation_status"
                ),
                "expected_rows": (
                    row_reconciliation.get(
                        "expected_rows"
                    )
                ),
                "actual_rows": (
                    row_reconciliation.get(
                        "actual_rows"
                    )
                ),
                "row_difference": (
                    row_reconciliation.get(
                        "row_difference"
                    )
                ),
                "row_match_percentage": (
                    row_reconciliation.get(
                        "match_percentage"
                    )
                ),
                "expected_columns": (
                    column_reconciliation.get(
                        "expected_columns"
                    )
                ),
                "actual_columns": (
                    column_reconciliation.get(
                        "actual_columns"
                    )
                ),
                "column_difference": (
                    column_reconciliation.get(
                        "column_difference"
                    )
                ),
                "issues": dataset.get(
                    "reconciliation_issues",
                    [],
                ),
            }
        )

    return {
        "summary": summary,
        "datasets": datasets,
        "extra_target_datasets": (
            reconciliation_output.get(
                "extra_target_datasets",
                [],
            )
        ),
    }

# ============================================================
# DISCOVERY REPORT MODEL
# ============================================================

def build_discovery_report_model(
    discovery_output: Dict[str, Any],
    growth_output: Dict[str, Any],
    requirements_output: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build report-friendly database discovery information.
    """

    return {
        "summary": discovery_output.get(
            "summary",
            {},
        ),
        "datasets": discovery_output.get(
            "datasets",
            [],
        ),
        "growth": growth_output,
        "requirements": requirements_output,
    }
# ============================================================
# ASSESSMENT REPORT MODEL
# ============================================================

def build_assessment_report_model(
    assessment_output: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build report-friendly assessment information.
    """

    return {
        "summary": assessment_output[
            "assessment_summary"
        ],
        "risk": assessment_output.get(
            "risk_assessment",
            {},
        ),
        "complexity": assessment_output.get(
            "complexity_assessment",
            {},
        ),
        "readiness": assessment_output.get(
            "readiness_assessment",
            {},
        ),
    }


# ============================================================
# RECOMMENDATION REPORT MODEL
# ============================================================

def build_recommendation_report_model(
    recommendation_output: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build report-friendly recommendation information.
    """

    recommendations = (
        recommendation_output.get(
            "recommendations",
            [],
        )
    )

    return {
        "decision_summary": (
            recommendation_output.get(
                "decision_summary",
                {},
            )
        ),
        "summary": recommendation_output[
            "recommendation_summary"
        ],
        "recommendations": recommendations,
    }


# ============================================================
# EXECUTIVE SUMMARY MODEL
# ============================================================

def build_executive_summary(
    database: str,
    profiling_model: Dict[str, Any],
    reconciliation_model: Dict[str, Any],
    assessment_model: Dict[str, Any],
    recommendation_model: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Build high-level business-facing summary information.
    """

    profiling_summary = profiling_model[
        "summary"
    ]

    reconciliation_summary = (
        reconciliation_model["summary"]
    )

    assessment_summary = assessment_model[
        "summary"
    ]

    recommendation_summary = (
        recommendation_model["summary"]
    )

    return {
        "database": database,
        "assessment_status": (
            assessment_summary.get(
                "assessment_status"
            )
        ),
        "risk_level": (
            assessment_summary.get(
                "risk_level"
            )
        ),
        "complexity_level": (
            assessment_summary.get(
                "complexity_level"
            )
        ),
        "readiness_score": (
            assessment_summary.get(
                "readiness_score"
            )
        ),
        "readiness_level": (
            assessment_summary.get(
                "readiness_level"
            )
        ),
        "total_source_datasets": (
            profiling_summary.get(
                "total_files_found",
                0,
            )
        ),
        "total_source_rows": (
            profiling_summary.get(
                "total_rows",
                0,
            )
        ),
        "total_data_quality_issues": (
            profiling_summary.get(
                "total_profiling_issues",
                0,
            )
        ),
        "reconciled_datasets": (
            reconciliation_summary.get(
                "reconciled_datasets",
                0,
            )
        ),
        "not_reconciled_datasets": (
            reconciliation_summary.get(
                "not_reconciled_datasets",
                0,
            )
        ),
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
        "total_recommendations": (
            recommendation_summary.get(
                "total_recommendations",
                0,
            )
        ),
        "critical_recommendations": (
            recommendation_summary.get(
                "critical_priority",
                0,
            )
        ),
        "high_recommendations": (
            recommendation_summary.get(
                "high_priority",
                0,
            )
        ),
    }


# ============================================================
# MAIN REPORT DATA BUILDER
# ============================================================

def build_report_data(
    database: str,
) -> Dict[str, Any]:
    """
    Build the complete common report model.
    """

    if database not in SUPPORTED_DATABASES:

        raise ValueError(
            f"Unsupported database: {database}"
        )

    report_inputs = load_report_inputs(
        database
    )

    current_build_number = os.environ.get("BUILD_NUMBER")

    validate_report_inputs(
        database,
        report_inputs,
        current_build_number,
    )

    profiling_model = (
        build_profiling_report_model(
            report_inputs["profiling"]
        )
    )

    reconciliation_model = (
        build_reconciliation_report_model(
            report_inputs["reconciliation"]
        )
    )

    assessment_model = (
        build_assessment_report_model(
            report_inputs["assessment"]
        )
    )

    recommendation_model = (
        build_recommendation_report_model(
            report_inputs["recommendation"]
        )
    )
    discovery_model = (
        build_discovery_report_model(
            report_inputs["discovery"],
            report_inputs["growth"],
            report_inputs["requirements"],
        )
    )

    executive_summary = build_executive_summary(
        database,
        profiling_model,
        reconciliation_model,
        assessment_model,
        recommendation_model,
    )

    return {
        "database": database,
        "executive_summary": executive_summary,
        "profiling": profiling_model,
        "reconciliation": reconciliation_model,
        "assessment": assessment_model,
        "recommendation": recommendation_model,
        "discovery": discovery_model,
    }