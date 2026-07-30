"""
Migration Requirement Analyzer.

Reads business-defined migration requirements for:

- Data Retention
- Archive Requirements
- Maximum Migration Duration SLA
- Maximum Downtime SLA

Supported Databases:
- MySQL
- PostgreSQL
- MongoDB
- MSSQL
"""

import argparse
import json
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = Path(__file__).resolve().parents[2]


# ============================================================
# SUPPORTED DATABASES
# ============================================================

SUPPORTED_DATABASES = {
    "mysql",
    "postgresql",
    "mongodb",
    "mssql",
}


# ============================================================
# CONFIGURATION PATH
# ============================================================

REQUIREMENTS_FILE = (
    ROOT
    / "config"
    / "discovery"
    / "migration_requirements.json"
)


# ============================================================
# LOAD JSON
# ============================================================

def load_json(
    file_path: Path,
) -> Dict[str, Any]:

    with file_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ============================================================
# SAVE JSON
# ============================================================

def save_json(
    file_path: Path,
    data: Dict[str, Any],
) -> None:

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with file_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False,
        )


# ============================================================
# VALIDATE RETENTION REQUIREMENTS
# ============================================================

def validate_retention_requirements(
    requirements: Dict[str, Any],
) -> Dict[str, Any]:

    required_retention_days = requirements.get(
        "required_retention_days"
    )

    archive_required = requirements.get(
        "archive_required"
    )

    if not isinstance(
        required_retention_days,
        int,
    ):

        raise ValueError(
            "required_retention_days must be an integer."
        )

    if required_retention_days < 0:

        raise ValueError(
            "required_retention_days cannot be negative."
        )

    if not isinstance(
        archive_required,
        bool,
    ):

        raise ValueError(
            "archive_required must be true or false."
        )

    return {
        "required_retention_days": (
            required_retention_days
        ),
        "archive_required": archive_required,
    }


# ============================================================
# VALIDATE SLA REQUIREMENTS
# ============================================================

def validate_sla_requirements(
    requirements: Dict[str, Any],
) -> Dict[str, Any]:

    maximum_migration_duration = requirements.get(
        "maximum_migration_duration_minutes"
    )

    maximum_downtime = requirements.get(
        "maximum_downtime_minutes"
    )

    if not isinstance(
        maximum_migration_duration,
        int,
    ):

        raise ValueError(
            "maximum_migration_duration_minutes "
            "must be an integer."
        )

    if maximum_migration_duration <= 0:

        raise ValueError(
            "maximum_migration_duration_minutes "
            "must be greater than zero."
        )

    if not isinstance(
        maximum_downtime,
        int,
    ):

        raise ValueError(
            "maximum_downtime_minutes "
            "must be an integer."
        )

    if maximum_downtime < 0:

        raise ValueError(
            "maximum_downtime_minutes "
            "cannot be negative."
        )

    return {
        "maximum_migration_duration_minutes": (
            maximum_migration_duration
        ),
        "maximum_downtime_minutes": (
            maximum_downtime
        ),
    }


# ============================================================
# ANALYZE REQUIREMENTS
# ============================================================

def analyze_requirements(
    database: str,
    configuration: Dict[str, Any],
) -> Dict[str, Any]:

    database_requirements = configuration.get(
        database
    )

    if database_requirements is None:

        raise ValueError(
            f"Requirements not configured for: {database}"
        )

    retention_configuration = (
        database_requirements.get(
            "retention_requirements"
        )
    )

    if retention_configuration is None:

        raise ValueError(
            "retention_requirements not configured "
            f"for: {database}"
        )

    sla_configuration = (
        database_requirements.get(
            "sla_requirements"
        )
    )

    if sla_configuration is None:

        raise ValueError(
            "sla_requirements not configured "
            f"for: {database}"
        )

    retention_requirements = (
        validate_retention_requirements(
            retention_configuration
        )
    )

    sla_requirements = (
        validate_sla_requirements(
            sla_configuration
        )
    )

    return {
        "database": database,
        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "requirement_status": "VALID",
        "retention_requirements": (
            retention_requirements
        ),
        "sla_requirements": (
            sla_requirements
        ),
    }


# ============================================================
# COMMAND LINE ARGUMENTS
# ============================================================

def parse_arguments():

    parser = argparse.ArgumentParser(
        description=(
            "Migration Requirement Analyzer"
        )
    )

    parser.add_argument(
        "--database",
        required=True,
        choices=sorted(
            SUPPORTED_DATABASES
        ),
        help="Target database",
    )

    return parser.parse_args()


# ============================================================
# MAIN
# ============================================================

def main():

    arguments = parse_arguments()

    database = arguments.database.lower()

    output_file = (
        ROOT
        / "metadata"
        / "discovery"
        / database
        / "requirements_analysis.json"
    )

    print()
    print(
        "====================================="
    )
    print(
        "MIGRATION REQUIREMENT ANALYSIS STARTED"
    )
    print(
        "====================================="
    )
    print(
        f"Database: {database}"
    )
    print()

    try:

        if not REQUIREMENTS_FILE.exists():

            raise FileNotFoundError(
                "Migration requirements configuration "
                f"not found: {REQUIREMENTS_FILE}"
            )

        configuration = load_json(
            REQUIREMENTS_FILE
        )

        output = analyze_requirements(
            database,
            configuration,
        )

        save_json(
            output_file,
            output,
        )

        retention = output[
            "retention_requirements"
        ]

        sla = output[
            "sla_requirements"
        ]

        print(
            "Retention Requirements:"
        )

        print(
            f"  Required Retention Days : "
            f"{retention['required_retention_days']}"
        )

        print(
            f"  Archive Required        : "
            f"{retention['archive_required']}"
        )

        print()

        print(
            "SLA Requirements:"
        )

        print(
            f"  Maximum Migration Time  : "
            f"{sla['maximum_migration_duration_minutes']} minutes"
        )

        print(
            f"  Maximum Downtime        : "
            f"{sla['maximum_downtime_minutes']} minutes"
        )

        print()
        print(
            "====================================="
        )
        print(
            "MIGRATION REQUIREMENT ANALYSIS COMPLETED"
        )
        print(
            "====================================="
        )

        print(
            f"Output: {output_file}"
        )

        print()

    except Exception as error:

        print(
            "====================================="
        )
        print(
            "MIGRATION REQUIREMENT ANALYSIS FAILED"
        )
        print(
            "====================================="
        )

        print(
            f"Error: {error}"
        )

        print()

        sys.exit(1)


if __name__ == "__main__":
    main()