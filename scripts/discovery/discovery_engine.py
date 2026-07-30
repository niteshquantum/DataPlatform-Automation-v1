"""
Database Discovery Engine.

Collects migration discovery information from supported databases:

- Table / Collection Counts
- Row / Document Counts
- Largest Tables / Collections

Supported Databases:
- MySQL
- PostgreSQL
- MongoDB
- MSSQL
"""

import argparse
import importlib
import json
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(ROOT),
)


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
# DATABASE CONNECTION MODULES
# ============================================================

CONNECTION_MODULES = {
    "mysql": (
        "scripts.python.mysql.setup.db_connection"
    ),
    "postgresql": (
        "scripts.python.postgresql.setup.db_connection"
    ),
    "mongodb": (
        "scripts.python.mongodb.setup.db_connection"
    ),
    "mssql": (
        "scripts.python.mssql.setup.db_connection"
    ),
}


# ============================================================
# CONNECTION MODULE LOADER
# ============================================================

def load_connection_module(
    database: str,
):
    """
    Dynamically load the existing database connection module.
    """

    module_path = CONNECTION_MODULES.get(database)

    if not module_path:

        raise ValueError(
            f"Unsupported database: {database}"
        )

    try:

        return importlib.import_module(
            module_path
        )

    except ModuleNotFoundError as error:

        raise RuntimeError(
            "Database connection module could not be loaded. "
            f"Expected module: {module_path}"
        ) from error


# ============================================================
# MYSQL DISCOVERY
# ============================================================

def discover_mysql(
    connection_module,
) -> List[Dict[str, Any]]:
    """
    Discover MySQL tables and row counts.
    """

    connection = None
    cursor = None

    try:

        connection = (
            connection_module.get_connection()
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT TABLE_NAME
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            AND table_type = 'BASE TABLE'
            AND LOWER(TABLE_NAME) NOT IN (
                'databasechangelog',
                'databasechangeloglock'
            )
            ORDER BY TABLE_NAME
            """
        )

        table_names = [
            row[0]
            for row in cursor.fetchall()
        ]

        datasets = []

        for table_name in table_names:

            safe_table_name = (
                table_name.replace(
                    "`",
                    "``",
                )
            )

            cursor.execute(
                f"SELECT COUNT(*) "
                f"FROM `{safe_table_name}`"
            )

            row_count = int(
                cursor.fetchone()[0]
            )

            datasets.append(
                {
                    "dataset_name": table_name,
                    "dataset_type": "TABLE",
                    "record_count": row_count,
                }
            )

        return datasets

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# POSTGRESQL DISCOVERY
# ============================================================

def discover_postgresql(
    connection_module,
) -> List[Dict[str, Any]]:
    """
    Discover PostgreSQL public-schema tables
    and row counts.
    """

    connection = None
    cursor = None

    try:

        connection = (
            connection_module.get_connection()
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            AND LOWER(table_name) NOT IN (
                'databasechangelog',
                'databasechangeloglock'
            )
            ORDER BY table_name
            """
        )

        table_names = [
            row[0]
            for row in cursor.fetchall()
        ]

        datasets = []

        for table_name in table_names:

            safe_table_name = (
                table_name.replace(
                    '"',
                    '""',
                )
            )

            cursor.execute(
                f'SELECT COUNT(*) '
                f'FROM "{safe_table_name}"'
            )

            row_count = int(
                cursor.fetchone()[0]
            )

            datasets.append(
                {
                    "dataset_name": table_name,
                    "dataset_type": "TABLE",
                    "record_count": row_count,
                }
            )

        return datasets

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# MONGODB DISCOVERY
# ============================================================

def discover_mongodb(
    connection_module,
) -> List[Dict[str, Any]]:
    """
    Discover MongoDB collections and document counts.
    """

    database = connection_module.get_db()

    collection_names = sorted(
        database.list_collection_names()
    )

    datasets = []

    for collection_name in collection_names:

        document_count = int(
            database[
                collection_name
            ].count_documents({})
        )

        datasets.append(
            {
                "dataset_name": collection_name,
                "dataset_type": "COLLECTION",
                "record_count": document_count,
            }
        )

    return datasets


# ============================================================
# MSSQL DISCOVERY
# ============================================================

def discover_mssql(
    connection_module,
) -> List[Dict[str, Any]]:
    """
    Discover MSSQL user tables and row counts.
    """

    connection = None
    cursor = None

    try:

        connection = (
            connection_module.get_connection()
        )

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT TABLE_SCHEMA, TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            ORDER BY TABLE_SCHEMA, TABLE_NAME
            """
        )

        table_details = cursor.fetchall()

        datasets = []

        for schema_name, table_name in table_details:

            safe_schema = (
                schema_name.replace(
                    "]",
                    "]]",
                )
            )

            safe_table = (
                table_name.replace(
                    "]",
                    "]]",
                )
            )

            cursor.execute(
                f"SELECT COUNT(*) "
                f"FROM [{safe_schema}].[{safe_table}]"
            )

            row_count = int(
                cursor.fetchone()[0]
            )

            datasets.append(
                {
                    "dataset_name": table_name,
                    "schema_name": schema_name,
                    "dataset_type": "TABLE",
                    "record_count": row_count,
                }
            )

        return datasets

    finally:

        if cursor is not None:
            cursor.close()

        if connection is not None:
            connection.close()


# ============================================================
# DATABASE DISCOVERY DISPATCHER
# ============================================================

def discover_database(
    database: str,
    connection_module,
) -> List[Dict[str, Any]]:
    """
    Execute database-specific discovery.
    """

    discovery_functions = {
        "mysql": discover_mysql,
        "postgresql": discover_postgresql,
        "mongodb": discover_mongodb,
        "mssql": discover_mssql,
    }

    discovery_function = (
        discovery_functions[database]
    )

    return discovery_function(
        connection_module
    )


# ============================================================
# DISCOVERY SUMMARY
# ============================================================

def build_discovery_summary(
    datasets: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build database discovery summary.
    """

    total_datasets = len(datasets)

    total_records = sum(
        int(
            dataset.get(
                "record_count",
                0,
            )
        )
        for dataset in datasets
    )

    largest_datasets = sorted(
        datasets,
        key=lambda dataset: int(
            dataset.get(
                "record_count",
                0,
            )
        ),
        reverse=True,
    )[:10]

    return {
        "total_datasets": total_datasets,
        "total_records": total_records,
        "largest_datasets": (
            largest_datasets
        ),
    }


# ============================================================
# DISCOVERY OUTPUT
# ============================================================

def build_discovery_output(
    database: str,
    datasets: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build final discovery JSON output.
    """

    summary = build_discovery_summary(
        datasets
    )

    return {
        "database": database,
        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "discovery_status": "SUCCESS",
        "summary": summary,
        "datasets": datasets,
    }


# ============================================================
# SAVE OUTPUT
# ============================================================

def save_discovery_output(
    database: str,
    output: Dict[str, Any],
) -> Path:
    """
    Save discovery output to metadata directory.
    """

    output_directory = (
        ROOT
        / "metadata"
        / "discovery"
        / database
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        output_directory
        / "discovery.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            indent=4,
            ensure_ascii=False,
        )

    return output_file


# ============================================================
# COMMAND LINE ARGUMENTS
# ============================================================

def parse_arguments():

    parser = argparse.ArgumentParser(
        description=(
            "Database Discovery Engine"
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

    print()
    print(
        "====================================="
    )
    print(
        "DATABASE DISCOVERY STARTED"
    )
    print(
        "====================================="
    )
    print(
        f"Database: {database}"
    )
    print()

    try:

        connection_module = (
            load_connection_module(
                database
            )
        )

        datasets = discover_database(
            database,
            connection_module,
        )

        output = build_discovery_output(
            database,
            datasets,
        )

        output_file = save_discovery_output(
            database,
            output,
        )

        summary = output["summary"]

        print(
            "====================================="
        )
        print(
            "DATABASE DISCOVERY COMPLETED"
        )
        print(
            "====================================="
        )
        print(
            f"Database       : {database}"
        )
        print(
            f"Total Datasets : "
            f"{summary['total_datasets']}"
        )
        print(
            f"Total Records  : "
            f"{summary['total_records']}"
        )

        print()
        print(
            "Largest Datasets:"
        )

        for dataset in summary[
            "largest_datasets"
        ]:

            print(
                f"  "
                f"{dataset['dataset_name']:<30} "
                f"{dataset['record_count']}"
            )

        print()
        print(
            f"Output          : {output_file}"
        )
        print()

    except Exception as error:

        print(
            "====================================="
        )
        print(
            "DATABASE DISCOVERY FAILED"
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