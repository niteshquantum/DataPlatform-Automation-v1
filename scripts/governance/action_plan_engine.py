"""
Migration Action Plan and Decision Governance Engine.

Converts migration recommendations into governed action items
for technical teams, data owners, business stakeholders, and
migration decision-makers.

Generates:
    metadata/governance/<database>/action_plan.json
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# CONSTANTS
# ============================================================

SUPPORTED_DATABASES = (
    "mysql",
    "postgresql",
    "mssql",
    "mongodb",
)


OWNER_MAPPING = {
    "DATA_QUALITY": "DATA_OWNER",
    "DATA_AVAILABILITY": "SOURCE_SYSTEM_OWNER",
    "DATA_RECONCILIATION": "MIGRATION_ENGINEER",
    "SCHEMA_RECONCILIATION": "DATABASE_ENGINEER",
    "MIGRATION_COMPLETENESS": "MIGRATION_ENGINEER",
    "MIGRATION_SCOPE": "MIGRATION_MANAGER",
    "MIGRATION_RISK": "MIGRATION_MANAGER",
    "MIGRATION_COMPLEXITY": "TECHNICAL_LEAD",
    "MIGRATION_READINESS": "MIGRATION_MANAGER",
}


# ============================================================
# JSON LOADER
# ============================================================

def load_json_file(
    file_path: Path,
    input_name: str,
) -> Dict[str, Any]:

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

def load_action_plan_inputs(
    database: str,
) -> Dict[str, Any]:

    recommendation_file = (
        PROJECT_ROOT
        / "metadata"
        / "recommendation"
        / database
        / "recommendation.json"
    )

    return load_json_file(
        recommendation_file,
        "Recommendation output",
    )


# ============================================================
# INPUT VALIDATION
# ============================================================

def validate_action_plan_input(
    database: str,
    recommendation_output: Dict[str, Any],
) -> None:

    if "recommendation_metadata" not in recommendation_output:

        raise ValueError(
            "recommendation_metadata is missing "
            "from recommendation output."
        )

    if "recommendations" not in recommendation_output:

        raise ValueError(
            "recommendations are missing "
            "from recommendation output."
        )

    input_database = (
        recommendation_output[
            "recommendation_metadata"
        ].get("database")
    )

    if input_database != database:

        raise ValueError(
            "Recommendation output database does not "
            f"match selected database '{database}'."
        )


# ============================================================
# OWNER DETERMINATION
# ============================================================

def determine_suggested_owner(
    category: str,
) -> str:

    return OWNER_MAPPING.get(
        category,
        "MIGRATION_TEAM",
    )


# ============================================================
# APPROVAL BLOCKING DETERMINATION
# ============================================================

def determine_approval_blocking(
    priority: str,
    category: str,
) -> bool:

    if priority in (
        "CRITICAL",
        "HIGH",
    ):
        return True

    blocking_categories = {
        "MIGRATION_COMPLETENESS",
        "SCHEMA_RECONCILIATION",
    }

    return category in blocking_categories


# ============================================================
# RESOLUTION REQUIREMENT
# ============================================================

def determine_resolution_requirement(
    approval_blocking: bool,
) -> str:

    if approval_blocking:

        return "MUST_RESOLVE_BEFORE_APPROVAL"

    return "REVIEW_AND_TRACK"


# ============================================================
# ACTION ITEM CREATION
# ============================================================

def create_action_item(
    recommendation: Dict[str, Any],
    action_number: int,
) -> Dict[str, Any]:

    priority = recommendation.get(
        "priority",
        "LOW",
    )

    category = recommendation.get(
        "category",
        "UNCLASSIFIED",
    )

    suggested_owner = (
        determine_suggested_owner(
            category
        )
    )

    approval_blocking = (
        determine_approval_blocking(
            priority,
            category,
        )
    )

    resolution_requirement = (
        determine_resolution_requirement(
            approval_blocking
        )
    )

    return {
        "action_id": (
            f"ACT-{action_number:03d}"
        ),
        "recommendation_id": (
            recommendation.get(
                "recommendation_id"
            )
        ),
        "title": recommendation.get(
            "title"
        ),
        "category": category,
        "priority": priority,
        "suggested_owner": suggested_owner,
        "approval_blocking": approval_blocking,
        "resolution_requirement": (
            resolution_requirement
        ),
        "action_status": "OPEN",
        "dataset": recommendation.get(
            "dataset"
        ),
        "column": recommendation.get(
            "column"
        ),
        "finding": recommendation.get(
            "finding"
        ),
        "business_impact": recommendation.get(
            "business_impact"
        ),
        "required_action": recommendation.get(
            "recommended_action"
        ),
        "next_step": recommendation.get(
            "next_step"
        ),
        "source": recommendation.get(
            "source"
        ),
    }


# ============================================================
# GOVERNANCE DECISION
# ============================================================

def determine_governance_decision(
    blocking_actions: int,
    open_actions: int,
) -> str:

    if blocking_actions > 0:

        return "APPROVAL_BLOCKED"

    if open_actions > 0:

        return "APPROVAL_WITH_ACTIONS"

    return "APPROVAL_READY"


# ============================================================
# ACTION PLAN ENGINE
# ============================================================

def run_action_plan_engine(
    database: str,
) -> Dict[str, Any]:

    print()
    print("=====================================")
    print("ACTION PLAN ENGINE STARTED")
    print("=====================================")
    print(f"Database: {database}")
    print()

    recommendation_output = (
        load_action_plan_inputs(
            database
        )
    )

    validate_action_plan_input(
        database,
        recommendation_output,
    )

    recommendations = (
        recommendation_output.get(
            "recommendations",
            [],
        )
    )

    action_items: List[
        Dict[str, Any]
    ] = []

    for action_number, recommendation in enumerate(
        recommendations,
        start=1,
    ):

        action_items.append(
            create_action_item(
                recommendation,
                action_number,
            )
        )

    total_actions = len(
        action_items
    )

    open_actions = sum(
        1
        for action in action_items
        if action["action_status"] == "OPEN"
    )

    blocking_actions = sum(
        1
        for action in action_items
        if action["approval_blocking"]
    )

    critical_actions = sum(
        1
        for action in action_items
        if action["priority"] == "CRITICAL"
    )

    high_actions = sum(
        1
        for action in action_items
        if action["priority"] == "HIGH"
    )

    medium_actions = sum(
        1
        for action in action_items
        if action["priority"] == "MEDIUM"
    )

    low_actions = sum(
        1
        for action in action_items
        if action["priority"] == "LOW"
    )

    governance_decision = (
        determine_governance_decision(
            blocking_actions,
            open_actions,
        )
    )

    output_directory = (
        PROJECT_ROOT
        / "metadata"
        / "governance"
        / database
    )

    output_file = (
        output_directory
        / "action_plan.json"
    )

    action_plan_output = {
        "action_plan_metadata": {
            "database": database,
            "generated_at_utc": datetime.now(
                timezone.utc
            ).isoformat(),
            "action_plan_version": "1.0",
        },
        "governance_summary": {
            "governance_decision": (
                governance_decision
            ),
            "total_actions": total_actions,
            "open_actions": open_actions,
            "blocking_actions": (
                blocking_actions
            ),
            "critical_actions": (
                critical_actions
            ),
            "high_actions": high_actions,
            "medium_actions": medium_actions,
            "low_actions": low_actions,
        },
        "action_items": action_items,
    }

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            action_plan_output,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print("=====================================")
    print("ACTION PLAN ENGINE COMPLETED")
    print("=====================================")
    print(f"Total Actions    : {total_actions}")
    print(f"Open Actions     : {open_actions}")
    print(f"Blocking Actions : {blocking_actions}")
    print(f"Critical Actions : {critical_actions}")
    print(f"High Actions     : {high_actions}")
    print(f"Medium Actions   : {medium_actions}")
    print(f"Low Actions      : {low_actions}")
    print(
        f"Governance       : "
        f"{governance_decision}"
    )
    print(f"Output           : {output_file}")
    print()

    return action_plan_output


# ============================================================
# COMMAND-LINE ARGUMENTS
# ============================================================

def parse_arguments() -> argparse.Namespace:

    parser = argparse.ArgumentParser(
        description=(
            "Generate migration governance "
            "action plan."
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        choices=SUPPORTED_DATABASES,
    )

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    arguments = parse_arguments()

    try:

        run_action_plan_engine(
            arguments.database
        )

    except Exception as error:

        print()
        print("=====================================")
        print("ACTION PLAN ENGINE FAILED")
        print("=====================================")
        print(f"Error: {error}")
        print()

        sys.exit(1)


if __name__ == "__main__":
    main()