"""
Migration Recommendation Engine.

Reads profiling, reconciliation, and assessment outputs and
converts technical findings into prioritized, actionable
migration recommendations.

Generates:
    metadata/recommendation/<database>/recommendation.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


# ============================================================
# PROJECT ROOT AND IMPORT SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# CONSTANTS
# ============================================================

SUPPORTED_DATABASES = (
    "mysql",
    "postgresql",
    "mssql",
    "mongodb",
)

PRIORITY_ORDER = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4,
}


# ============================================================
# JSON INPUT LOADER
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
# INPUT LOADING
# ============================================================

def load_recommendation_inputs(
    database: str,
) -> Dict[str, Dict[str, Any]]:
    """
    Load profiling, reconciliation, and assessment outputs.
    """

    profiling_file = (
        PROJECT_ROOT
        / "metadata"
        / "profiling"
        / database
        / "profiling.json"
    )

    reconciliation_file = (
        PROJECT_ROOT
        / "metadata"
        / "reconciliation"
        / database
        / "reconciliation.json"
    )

    assessment_file = (
        PROJECT_ROOT
        / "metadata"
        / "assessment"
        / database
        / "assessment.json"
    )

    return {
        "profiling": load_json_file(
            profiling_file,
            "Profiling output",
        ),
        "reconciliation": load_json_file(
            reconciliation_file,
            "Reconciliation output",
        ),
        "assessment": load_json_file(
            assessment_file,
            "Assessment output",
        ),
    }


# ============================================================
# INPUT VALIDATION
# ============================================================

def validate_recommendation_inputs(
    database: str,
    profiling_output: Dict[str, Any],
    reconciliation_output: Dict[str, Any],
    assessment_output: Dict[str, Any],
) -> None:
    """
    Validate required input structures and database ownership.
    """

    required_inputs = (
        (
            profiling_output,
            "profiling_metadata",
            "profiling_summary",
            "Profiling",
        ),
        (
            reconciliation_output,
            "reconciliation_metadata",
            "reconciliation_summary",
            "Reconciliation",
        ),
        (
            assessment_output,
            "assessment_metadata",
            "assessment_summary",
            "Assessment",
        ),
    )

    for (
        output,
        metadata_key,
        summary_key,
        input_name,
    ) in required_inputs:

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


# ============================================================
# RECOMMENDATION CREATION
# ============================================================

def create_recommendation(
    recommendation_id: str,
    category: str,
    priority: str,
    title: str,
    finding: str,
    business_impact: str,
    recommended_action: str,
    next_step: str,
    source: str,
    dataset: str = None,
    column: str = None,
) -> Dict[str, Any]:
    """
    Create a standardized actionable recommendation.
    """

    return {
        "recommendation_id": recommendation_id,
        "category": category,
        "priority": priority,
        "title": title,
        "finding": finding,
        "business_impact": business_impact,
        "recommended_action": recommended_action,
        "next_step": next_step,
        "source": source,
        "dataset": dataset,
        "column": column,
    }


# ============================================================
# PROFILING RECOMMENDATIONS
# ============================================================

def generate_profiling_recommendations(
    profiling_output: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate recommendations from profiling findings.
    """

    recommendations = []

    recommendation_number = 1

    for dataset in profiling_output.get(
        "datasets",
        [],
    ):

        dataset_name = Path(
            dataset["file_name"]
        ).stem

        for issue in dataset.get(
            "profiling_issues",
            [],
        ):

            issue_type = issue.get(
                "issue_type"
            )

            severity = issue.get(
                "severity",
                "LOW",
            )

            column = issue.get(
                "column"
            )

            recommendation_id = (
                f"PROF-{recommendation_number:03d}"
            )

            if issue_type == "NULL_VALUES":

                recommendations.append(
                    create_recommendation(
                        recommendation_id,
                        "DATA_QUALITY",
                        severity,
                        "Review Missing Data",
                        issue.get(
                            "message",
                            "Missing values were detected.",
                        ),
                        (
                            "Missing data may reduce data "
                            "completeness, reporting accuracy, "
                            "and downstream migration quality."
                        ),
                        (
                            "Review whether the affected field "
                            "is optional or mandatory. Define "
                            "an appropriate remediation rule "
                            "before final migration approval."
                        ),
                        (
                            "Assign the affected field to a "
                            "data owner for validation and "
                            "remediation."
                        ),
                        "PROFILING",
                        dataset_name,
                        column,
                    )
                )

            elif issue_type == "DUPLICATE_ROWS":

                recommendations.append(
                    create_recommendation(
                        recommendation_id,
                        "DATA_QUALITY",
                        severity,
                        "Resolve Duplicate Records",
                        issue.get(
                            "message",
                            "Duplicate records were detected.",
                        ),
                        (
                            "Duplicate records may create "
                            "incorrect totals, duplicate "
                            "transactions, and inconsistent "
                            "business reporting."
                        ),
                        (
                            "Identify the business key and "
                            "define a controlled deduplication "
                            "rule before migration approval."
                        ),
                        (
                            "Review duplicate records and "
                            "approve a deduplication strategy."
                        ),
                        "PROFILING",
                        dataset_name,
                    )
                )

            elif issue_type == "EMPTY_DATASET":

                recommendations.append(
                    create_recommendation(
                        recommendation_id,
                        "DATA_AVAILABILITY",
                        severity,
                        "Investigate Empty Dataset",
                        issue.get(
                            "message",
                            "The source dataset is empty.",
                        ),
                        (
                            "An empty dataset may indicate "
                            "missing source data, extraction "
                            "failure, or incomplete migration "
                            "scope."
                        ),
                        (
                            "Confirm whether the empty dataset "
                            "is expected and validate the source "
                            "extraction process."
                        ),
                        (
                            "Obtain confirmation from the "
                            "source system owner."
                        ),
                        "PROFILING",
                        dataset_name,
                    )
                )

            elif issue_type == "CONSTANT_COLUMN":

                recommendations.append(
                    create_recommendation(
                        recommendation_id,
                        "DATA_QUALITY",
                        severity,
                        "Review Constant Field",
                        issue.get(
                            "message",
                            "A constant field was detected.",
                        ),
                        (
                            "A constant field may be valid, "
                            "redundant, incorrectly populated, "
                            "or unsuitable for the target model."
                        ),
                        (
                            "Validate the business purpose of "
                            "the field and determine whether it "
                            "should be migrated."
                        ),
                        (
                            "Confirm field usage with the "
                            "relevant data owner."
                        ),
                        "PROFILING",
                        dataset_name,
                        column,
                    )
                )

            else:

                continue

            recommendation_number += 1

    return recommendations


# ============================================================
# RECONCILIATION RECOMMENDATIONS
# ============================================================

def generate_reconciliation_recommendations(
    reconciliation_output: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate recommendations from reconciliation findings.
    """

    recommendations = []

    recommendation_number = 1

    for dataset in reconciliation_output.get(
        "datasets",
        [],
    ):

        dataset_name = dataset.get(
            "dataset_name"
        )

        for issue in dataset.get(
            "reconciliation_issues",
            [],
        ):

            issue_type = issue.get(
                "issue_type"
            )

            severity = issue.get(
                "severity",
                "LOW",
            )

            recommendation_id = (
                f"RECON-{recommendation_number:03d}"
            )

            if issue_type == "ROW_COUNT_MISMATCH":

                recommendations.append(
                    create_recommendation(
                        recommendation_id,
                        "DATA_RECONCILIATION",
                        severity,
                        "Resolve Record Count Mismatch",
                        issue.get(
                            "message",
                            "Record counts do not match.",
                        ),
                        (
                            "Missing or additional records may "
                            "cause incomplete migration results "
                            "and unreliable business reporting."
                        ),
                        (
                            "Compare source and target records, "
                            "identify failed or duplicate loads, "
                            "and resolve the mismatch."
                        ),
                        (
                            "Perform record-level investigation "
                            "before migration approval."
                        ),
                        "RECONCILIATION",
                        dataset_name,
                    )
                )

            elif issue_type == "COLUMN_COUNT_MISMATCH":

                recommendations.append(
                    create_recommendation(
                        recommendation_id,
                        "SCHEMA_RECONCILIATION",
                        severity,
                        "Resolve Schema Mismatch",
                        issue.get(
                            "message",
                            "Source and target structures differ.",
                        ),
                        (
                            "Schema differences may result in "
                            "missing fields, incorrect mappings, "
                            "or data loss."
                        ),
                        (
                            "Review source-to-target schema "
                            "mapping and correct missing or "
                            "unexpected target fields."
                        ),
                        (
                            "Validate and approve the corrected "
                            "schema mapping."
                        ),
                        "RECONCILIATION",
                        dataset_name,
                    )
                )

            elif issue_type == "MISSING_TARGET_DATASET":

                recommendations.append(
                    create_recommendation(
                        recommendation_id,
                        "MIGRATION_COMPLETENESS",
                        severity,
                        "Load Missing Target Dataset",
                        issue.get(
                            "message",
                            "Expected target dataset is missing.",
                        ),
                        (
                            "Missing target data makes the "
                            "migration incomplete and may block "
                            "dependent business processes."
                        ),
                        (
                            "Investigate the load failure or "
                            "scope mismatch and load the missing "
                            "dataset."
                        ),
                        (
                            "Resolve the missing target dataset "
                            "before proceeding."
                        ),
                        "RECONCILIATION",
                        dataset_name,
                    )
                )

            else:

                continue

            recommendation_number += 1

    # --------------------------------------------------------
    # EXTRA TARGET DATASETS
    # --------------------------------------------------------

    # for target_name in reconciliation_output.get(
    #     "extra_target_datasets",
    #     [],
    # ):

    #     recommendation_id = (
    #         f"RECON-{recommendation_number:03d}"
    #     )

    #     recommendations.append(
    #         create_recommendation(
    #             recommendation_id,
    #             "MIGRATION_SCOPE",
    #             "MEDIUM",
    #             "Review Unexpected Target Dataset",
    #             (
    #                 f"Target dataset '{target_name}' "
    #                 "does not have a corresponding "
    #                 "incoming source dataset."
    #             ),
    #             (
    #                 "Unexpected target objects may indicate "
    #                 "scope inconsistency, legacy data, or "
    #                 "uncontrolled target content."
    #             ),
    #             (
    #                 "Confirm whether the target dataset is "
    #                 "expected, should be preserved, or should "
    #                 "be excluded from the migration scope."
    #             ),
    #             (
    #                 "Obtain migration scope confirmation "
    #                 "from the responsible owner."
    #             ),
    #             "RECONCILIATION",
    #             target_name,
    #         )
    #     )

    #     recommendation_number += 1

    return recommendations


# ============================================================
# STRATEGIC RECOMMENDATIONS
# ============================================================

def generate_strategic_recommendations(
    assessment_output: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate high-level recommendations from assessment results.
    """

    recommendations = []

    summary = assessment_output[
        "assessment_summary"
    ]

    risk_level = summary[
        "risk_level"
    ]

    complexity_level = summary[
        "complexity_level"
    ]

    readiness_level = summary[
        "readiness_level"
    ]

    if risk_level in (
        "HIGH",
        "CRITICAL",
    ):

        recommendations.append(
            create_recommendation(
                "STRAT-001",
                "MIGRATION_RISK",
                risk_level,
                "Reduce Migration Risk",
                (
                    f"The current migration risk "
                    f"level is {risk_level}."
                ),
                (
                    "High migration risk increases the "
                    "probability of data-quality issues, "
                    "rework, operational disruption, and "
                    "migration failure."
                ),
                (
                    "Resolve high-priority profiling and "
                    "reconciliation findings before final "
                    "migration approval."
                ),
                (
                    "Create and track a remediation plan "
                    "for all high-priority findings."
                ),
                "ASSESSMENT",
            )
        )

    if complexity_level in (
        "HIGH",
        "VERY_HIGH",
    ):

        recommendations.append(
            create_recommendation(
                "STRAT-002",
                "MIGRATION_COMPLEXITY",
                "HIGH",
                "Apply Enhanced Migration Controls",
                (
                    f"The migration complexity "
                    f"level is {complexity_level}."
                ),
                (
                    "Higher migration complexity may increase "
                    "delivery effort, testing requirements, "
                    "execution time, and operational risk."
                ),
                (
                    "Use phased execution, stronger validation, "
                    "and additional technical review controls."
                ),
                (
                    "Review the migration execution plan and "
                    "define additional controls."
                ),
                "ASSESSMENT",
            )
        )

    if readiness_level == "READY":

        recommendations.append(
            create_recommendation(
                "STRAT-003",
                "MIGRATION_READINESS",
                "LOW",
                "Proceed to Next Migration Stage",
                (
                    "The current assessment indicates "
                    "that the migration is ready."
                ),
                (
                    "Proceeding with validated inputs reduces "
                    "the likelihood of avoidable migration "
                    "issues."
                ),
                (
                    "Continue with the approved migration "
                    "process and maintain standard validation "
                    "controls."
                ),
                (
                    "Obtain approval to proceed to the "
                    "next migration stage."
                ),
                "ASSESSMENT",
            )
        )

    elif readiness_level == "READY_WITH_CONDITIONS":

        recommendations.append(
            create_recommendation(
                "STRAT-003",
                "MIGRATION_READINESS",
                "MEDIUM",
                "Proceed with Defined Conditions",
                (
                    "The migration is ready only with "
                    "specific conditions."
                ),
                (
                    "Unresolved conditions may create "
                    "avoidable migration or operational risk."
                ),
                (
                    "Document outstanding conditions, assign "
                    "owners, and track them through closure."
                ),
                (
                    "Obtain conditional approval with a "
                    "documented action plan."
                ),
                "ASSESSMENT",
            )
        )

    else:

        recommendations.append(
            create_recommendation(
                "STRAT-003",
                "MIGRATION_READINESS",
                "HIGH",
                "Complete Remediation Before Approval",
                (
                    f"The current migration readiness "
                    f"level is {readiness_level}."
                ),
                (
                    "Proceeding without remediation may result "
                    "in incomplete data, reporting issues, "
                    "operational disruption, or migration "
                    "failure."
                ),
                (
                    "Resolve priority findings and rerun "
                    "profiling, reconciliation, and assessment "
                    "before requesting migration approval."
                ),
                (
                    "Complete remediation and rerun the "
                    "migration assessment."
                ),
                "ASSESSMENT",
            )
        )

    return recommendations


# ============================================================
# PRIORITY SORTING
# ============================================================

def sort_recommendations(
    recommendations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Sort recommendations by business priority.
    """

    return sorted(
        recommendations,
        key=lambda recommendation: PRIORITY_ORDER.get(
            recommendation.get(
                "priority",
                "LOW",
            ),
            99,
        ),
    )


# ============================================================
# RECOMMENDATION ENGINE
# ============================================================

def run_recommendation_engine(
    database: str,
) -> Dict[str, Any]:
    """
    Generate actionable migration recommendations.
    """

    print()
    print("=====================================")
    print("RECOMMENDATION ENGINE STARTED")
    print("=====================================")
    print(f"Database: {database}")
    print()

    inputs = load_recommendation_inputs(
        database
    )

    profiling_output = inputs[
        "profiling"
    ]

    reconciliation_output = inputs[
        "reconciliation"
    ]

    assessment_output = inputs[
        "assessment"
    ]

    validate_recommendation_inputs(
        database,
        profiling_output,
        reconciliation_output,
        assessment_output,
    )

    profiling_recommendations = (
        generate_profiling_recommendations(
            profiling_output
        )
    )

    reconciliation_recommendations = (
        generate_reconciliation_recommendations(
            reconciliation_output
        )
    )

    strategic_recommendations = (
        generate_strategic_recommendations(
            assessment_output
        )
    )

    recommendations = sort_recommendations(
        profiling_recommendations
        + reconciliation_recommendations
        + strategic_recommendations
    )

    priority_summary = {
        "critical": sum(
            1
            for recommendation in recommendations
            if recommendation["priority"] == "CRITICAL"
        ),
        "high": sum(
            1
            for recommendation in recommendations
            if recommendation["priority"] == "HIGH"
        ),
        "medium": sum(
            1
            for recommendation in recommendations
            if recommendation["priority"] == "MEDIUM"
        ),
        "low": sum(
            1
            for recommendation in recommendations
            if recommendation["priority"] == "LOW"
        ),
    }

    assessment_summary = assessment_output[
        "assessment_summary"
    ]

    output_directory = (
        PROJECT_ROOT
        / "metadata"
        / "recommendation"
        / database
    )

    output_file = (
        output_directory
        / "recommendation.json"
    )

    recommendation_output = {
        "recommendation_metadata": {
            "database": database,
            "generated_at_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "recommendation_version": "1.0",
        },
        "decision_summary": {
            "assessment_status": (
                assessment_summary[
                    "assessment_status"
                ]
            ),
            "risk_level": (
                assessment_summary[
                    "risk_level"
                ]
            ),
            "complexity_level": (
                assessment_summary[
                    "complexity_level"
                ]
            ),
            "readiness_score": (
                assessment_summary[
                    "readiness_score"
                ]
            ),
            "readiness_level": (
                assessment_summary[
                    "readiness_level"
                ]
            ),
        },
        "recommendation_summary": {
            "total_recommendations": len(
                recommendations
            ),
            "critical_priority": (
                priority_summary["critical"]
            ),
            "high_priority": (
                priority_summary["high"]
            ),
            "medium_priority": (
                priority_summary["medium"]
            ),
            "low_priority": (
                priority_summary["low"]
            ),
        },
        "recommendations": recommendations,
    }

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    build_number = os.environ.get("BUILD_NUMBER")
    if build_number:
        recommendation_output["recommendation_metadata"]["pipeline_build_number"] = build_number

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            recommendation_output,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("=====================================")
    print("RECOMMENDATION ENGINE COMPLETED")
    print("=====================================")
    print(
        f"Total Recommendations : "
        f"{len(recommendations)}"
    )
    print(
        f"Critical Priority     : "
        f"{priority_summary['critical']}"
    )
    print(
        f"High Priority         : "
        f"{priority_summary['high']}"
    )
    print(
        f"Medium Priority       : "
        f"{priority_summary['medium']}"
    )
    print(
        f"Low Priority          : "
        f"{priority_summary['low']}"
    )
    print(
        f"Output                : "
        f"{output_file}"
    )
    print()

    return recommendation_output


# ============================================================
# COMMAND-LINE ARGUMENTS
# ============================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Generate prioritized migration "
            "recommendations."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        choices=SUPPORTED_DATABASES,
        help=(
            "Database whose migration recommendations "
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

        run_recommendation_engine(
            arguments.database
        )

    except Exception as error:

        print()
        print("=====================================")
        print("RECOMMENDATION ENGINE FAILED")
        print("=====================================")
        print(f"Error: {error}")
        print()

        sys.exit(1)


if __name__ == "__main__":
    main()