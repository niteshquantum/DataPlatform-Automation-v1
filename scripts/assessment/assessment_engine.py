"""
Migration Assessment Framework - Main Entry Point

Reads profiling and reconciliation outputs and generates
a consolidated migration assessment.

Current assessment inputs:
    - Data Profiling
    - Data Reconciliation

Assessment outputs:
    - Migration Risk
    - Migration Complexity
    - Migration Readiness

Discovery findings will be integrated later when the
Discovery module output contract becomes available.

Generates:
    metadata/assessment/<database>/assessment.json
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


# ============================================================
# PROJECT ROOT AND IMPORT SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from scripts.assessment.complexity_assessor import (
    assess_complexity,
)

from scripts.assessment.readiness_assessor import (
    assess_readiness,
)

from scripts.assessment.risk_assessor import (
    assess_risk,
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


# ============================================================
# JSON INPUT LOADER
# ============================================================

def load_json_file(
    file_path: Path,
    input_name: str,
) -> Dict[str, Any]:
    """
    Load and validate a required JSON input file.
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
# ASSESSMENT INPUT LOADER
# ============================================================

def load_assessment_inputs(
    database: str,
) -> Dict[str, Dict[str, Any]]:
    """
    Load profiling and reconciliation outputs.
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

    discovery_file = (
        PROJECT_ROOT
        / "metadata"
        / "discovery"
        / database
        / "discovery.json"
    )

    growth_file = (
        PROJECT_ROOT
        / "metadata"
        / "discovery"
        / database
        / "growth_analysis.json"
    )

    requirements_file = (
        PROJECT_ROOT
        / "metadata"
        / "discovery"
        / database
        / "requirements_analysis.json"
    )


    profiling_output = load_json_file(
        profiling_file,
        "Profiling output",
    )

    reconciliation_output = load_json_file(
        reconciliation_file,
        "Reconciliation output",
    )

    discovery_output = load_json_file(
        discovery_file,
        "Discovery output",
    )

    growth_output = load_json_file(
        growth_file,
        "Growth analysis output",
    )

    requirements_output = load_json_file(
        requirements_file,
        "Requirements analysis output",
    )


    return {
        "profiling": profiling_output,
        "reconciliation": reconciliation_output,
        "discovery": discovery_output,
        "growth": growth_output,
        "requirements": requirements_output,
    }


# ============================================================
# INPUT VALIDATION
# ============================================================

def validate_assessment_inputs(
    database: str,
    profiling_output: Dict[str, Any],
    reconciliation_output: Dict[str, Any],
) -> None:
    """
    Validate required assessment input structure and ensure
    that both inputs belong to the selected database.
    """

    if "profiling_summary" not in profiling_output:

        raise ValueError(
            "profiling_summary is missing "
            "from profiling output."
        )

    if "reconciliation_summary" not in reconciliation_output:

        raise ValueError(
            "reconciliation_summary is missing "
            "from reconciliation output."
        )

    profiling_database = (
        profiling_output
        .get("profiling_metadata", {})
        .get("database")
    )

    reconciliation_database = (
        reconciliation_output
        .get("reconciliation_metadata", {})
        .get("database")
    )

    if profiling_database != database:

        raise ValueError(
            "Profiling output database does not "
            f"match selected database '{database}'."
        )

    if reconciliation_database != database:

        raise ValueError(
            "Reconciliation output database does not "
            f"match selected database '{database}'."
        )


# ============================================================
# OVERALL ASSESSMENT STATUS
# ============================================================

def determine_assessment_status(
    risk_assessment: Dict[str, Any],
    readiness_assessment: Dict[str, Any],
) -> str:
    """
    Determine the overall migration assessment status.

    This is a high-level technical/business status and is
    separate from detailed recommendations generated later.
    """

    risk_level = risk_assessment[
        "risk_level"
    ]

    readiness_level = readiness_assessment[
        "readiness_level"
    ]

    if (
        risk_level == "CRITICAL"
        or readiness_level == "NOT_READY"
    ):

        return "ACTION_REQUIRED"

    if readiness_level == "NEEDS_REMEDIATION":

        return "REMEDIATION_REQUIRED"

    if readiness_level == "READY_WITH_CONDITIONS":

        return "CONDITIONAL_APPROVAL"

    return "READY_FOR_NEXT_STAGE"


# ============================================================
# ASSESSMENT ENGINE
# ============================================================

def run_assessment(
    database: str,
) -> Dict[str, Any]:
    """
    Run migration assessment for the selected database.
    """

    print()
    print("=====================================")
    print("MIGRATION ASSESSMENT STARTED")
    print("=====================================")
    print(f"Database: {database}")
    print()

    # --------------------------------------------------------
    # LOAD INPUTS
    # --------------------------------------------------------

    assessment_inputs = load_assessment_inputs(
        database
    )

    profiling_output = assessment_inputs[
        "profiling"
    ]

    reconciliation_output = assessment_inputs[
        "reconciliation"
    ]
    discovery_output = assessment_inputs[
    "discovery"
    ]

    growth_analysis = assessment_inputs[
        "growth"
    ]

    requirements_analysis = assessment_inputs[
        "requirements"
    ]
    # --------------------------------------------------------
    # VALIDATE INPUTS
    # --------------------------------------------------------

    validate_assessment_inputs(
        database,
        profiling_output,
        reconciliation_output,
    )

    profiling_summary = profiling_output[
        "profiling_summary"
    ]

    reconciliation_summary = (
        reconciliation_output[
            "reconciliation_summary"
        ]
    )

    discovery_summary = discovery_output.get(
        "summary",
        {},
    )

    # --------------------------------------------------------
    # RISK ASSESSMENT
    # --------------------------------------------------------

    print("Assessing Migration Risk...")

    risk_assessment = assess_risk(
    profiling_summary,
    reconciliation_summary,
    growth_analysis,
    requirements_analysis,
)

    print(
        f"Risk Score : "
        f"{risk_assessment['risk_score']}"
    )

    print(
        f"Risk Level : "
        f"{risk_assessment['risk_level']}"
    )

    print()

    # --------------------------------------------------------
    # COMPLEXITY ASSESSMENT
    # --------------------------------------------------------

    print("Assessing Migration Complexity...")

    complexity_assessment = assess_complexity(
    profiling_summary,
    reconciliation_summary,
    discovery_summary,
    growth_analysis,
    )

    print(
        f"Complexity Score : "
        f"{complexity_assessment['complexity_score']}"
    )

    print(
        f"Complexity Level : "
        f"{complexity_assessment['complexity_level']}"
    )

    print()

    # --------------------------------------------------------
    # READINESS ASSESSMENT
    # --------------------------------------------------------

    print("Assessing Migration Readiness...")

    readiness_assessment = assess_readiness(
    profiling_summary,
    reconciliation_summary,
    risk_assessment,
    complexity_assessment,
    requirements_analysis,
        )

    print(
        f"Readiness Score : "
        f"{readiness_assessment['readiness_score']}"
    )

    print(
        f"Readiness Level : "
        f"{readiness_assessment['readiness_level']}"
    )

    print()

    # --------------------------------------------------------
    # OVERALL STATUS
    # --------------------------------------------------------

    assessment_status = (
        determine_assessment_status(
            risk_assessment,
            readiness_assessment,
        )
    )

    # --------------------------------------------------------
    # OUTPUT LOCATION
    # --------------------------------------------------------

    output_directory = (
        PROJECT_ROOT
        / "metadata"
        / "assessment"
        / database
    )

    output_file = (
        output_directory
        / "assessment.json"
    )

    # --------------------------------------------------------
    # FINAL ASSESSMENT OUTPUT
    # --------------------------------------------------------

    assessment_metadata = {
        "database": database,
        "generated_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "assessment_version": "1.0",
        "assessment_inputs": {
            "profiling": str(
                PROJECT_ROOT
                / "metadata"
                / "profiling"
                / database
                / "profiling.json"
            ),
            "reconciliation": str(
                PROJECT_ROOT
                / "metadata"
                / "reconciliation"
                / database
                / "reconciliation.json"
            ),
            "discovery": str(
                PROJECT_ROOT
                / "metadata"
                / "discovery"
                / database
                / "discovery.json"
            ),
            "growth": str(
                PROJECT_ROOT
                / "metadata"
                / "discovery"
                / database
                / "growth_analysis.json"
            ),
            "requirements": str(
                PROJECT_ROOT
                / "metadata"
                / "discovery"
                / database
                / "requirements_analysis.json"
            ),
        },
    }

    build_number = os.environ.get("BUILD_NUMBER")
    if build_number:
        assessment_metadata["pipeline_build_number"] = build_number

    assessment_output = {
        "assessment_metadata": assessment_metadata,
        "assessment_summary": {
            "database": database,
            "assessment_status": (
                assessment_status
            ),
            "risk_score": risk_assessment[
                "risk_score"
            ],
            "risk_level": risk_assessment[
                "risk_level"
            ],
            "complexity_score": (
                complexity_assessment[
                    "complexity_score"
                ]
            ),
            "complexity_level": (
                complexity_assessment[
                    "complexity_level"
                ]
            ),
            "readiness_score": (
                readiness_assessment[
                    "readiness_score"
                ]
            ),
            "readiness_level": (
                readiness_assessment[
                    "readiness_level"
                ]
            ),
        },
        "risk_assessment": risk_assessment,
        "complexity_assessment": (
            complexity_assessment
        ),
        "readiness_assessment": (
            readiness_assessment
        ),
    }

    # --------------------------------------------------------
    # WRITE OUTPUT
    # --------------------------------------------------------

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            assessment_output,
            file,
            indent=4,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # COMPLETION SUMMARY
    # --------------------------------------------------------

    print("=====================================")
    print("MIGRATION ASSESSMENT COMPLETED")
    print("=====================================")

    print(
        f"Database         : {database}"
    )

    print(
        f"Risk Level       : "
        f"{risk_assessment['risk_level']}"
    )

    print(
        f"Complexity Level : "
        f"{complexity_assessment['complexity_level']}"
    )

    print(
        f"Readiness Score  : "
        f"{readiness_assessment['readiness_score']}"
    )

    print(
        f"Readiness Level  : "
        f"{readiness_assessment['readiness_level']}"
    )

    print(
        f"Overall Status   : "
        f"{assessment_status}"
    )

    print(
        f"Output           : {output_file}"
    )

    print()

    return assessment_output


# ============================================================
# COMMAND-LINE ARGUMENTS
# ============================================================

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Assess migration risk, complexity, "
            "and readiness for the selected database."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        choices=SUPPORTED_DATABASES,
        help=(
            "Database whose migration readiness "
            "should be assessed."
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

        run_assessment(
            arguments.database
        )

    except Exception as error:

        print()
        print("=====================================")
        print("MIGRATION ASSESSMENT FAILED")
        print("=====================================")

        print(f"Error: {error}")

        print()

        sys.exit(1)


if __name__ == "__main__":
    main()