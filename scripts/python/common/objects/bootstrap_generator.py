import json
import shutil
import sys

from object_detector import ObjectDetector
from database_capabilities import supports_object
from generate_liquibase_objects import generate_liquibase_objects

from generators.generate_views import generate_views
from generators.generate_functions import generate_functions
from generators.generate_procedures import generate_procedures
from generators.generate_triggers import generate_triggers
from generators.generate_events import generate_events
from generators.generate_indexes import generate_indexes
from generators.generate_materialized_views import generate_materialized_views
from generators.generate_extensions import generate_extensions
from generate_master_objects import generate_master_objects

from config_loader import get_project_root, load_database_config


# ============================================================
# BOOTSTRAP GENERATOR
#
# Responsibility: GENERATION ONLY.
#
# This script:
#   1. Detects available schema metadata
#   2. Generates SQL object files (generated/)
#   3. Generates Liquibase XML changesets
#   4. Generates master_objects.xml
#
# It does NOT deploy or validate.
# Deployment is handled by deploy_objects.py.
# Validation is handled by validate_objects.py.
#
# The calling BAT/Bash wrapper orchestrates the full sequence:
#   bootstrap_generator.py <database>
#       -> deploy_objects.py <database>
#       -> validate_objects.py <database>
#
# Separating generation from deployment prevents Liquibase
# from executing twice when called through the pipeline.
# ============================================================


def _get_target_table_columns(database, table_name):

    db = database.lower()

    config = load_database_config(db)

    if db == "mysql":

        import mysql.connector

        conn = mysql.connector.connect(
            host=config["MYSQL_HOST"],
            port=int(config["MYSQL_PORT"]),
            user=config["MYSQL_USER"],
            password=config["MYSQL_PASSWORD"],
            database=config["MYSQL_DB"]
        )

        cursor = conn.cursor()

        cursor.execute(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s",
            (
                config["MYSQL_DB"],
                table_name
            )
        )

        columns = [
            row[0]
            for row in cursor.fetchall()
        ]

        cursor.close()
        conn.close()

        return columns

    if db == "mssql":

        import pyodbc

        conn_str = (
            f"DRIVER={{{config['MSSQL_ODBC_DRIVER']}}};"
            f"SERVER={config['MSSQL_HOST']},{config['MSSQL_PORT']};"
            f"DATABASE={config['MSSQL_DB']};"
            f"UID={config['MSSQL_USER']};"
            f"PWD={config['MSSQL_PASSWORD']};"
            "Encrypt=no;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=30;"
        )

        conn = pyodbc.connect(conn_str)

        cursor = conn.cursor()

        cursor.execute(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_CATALOG = ? AND TABLE_NAME = ?",
            (
                config["MSSQL_DB"],
                table_name
            )
        )

        columns = [
            row[0]
            for row in cursor.fetchall()
        ]

        cursor.close()
        conn.close()

        return columns

    return []


def _reconcile_schema_registry(database):

    root = get_project_root()

    registry_path = (
        root
        / "metadata"
        / database
        / "schema_registry.json"
    )

    if not registry_path.exists():

        return

    with open(
        registry_path,
        "r",
        encoding="utf-8"
    ) as file:

        registry = json.load(file)

    for table_name, columns in list(registry.items()):

        try:

            actual_columns = _get_target_table_columns(
                database,
                table_name
            )

        except Exception as exc:

            print(
                f"WARNING: failed to query target columns for "
                f"{table_name}: {exc}"
            )

            actual_columns = []

        if actual_columns:

            actual_set = {
                c.lower()
                for c in actual_columns
            }

            filtered = [
                c
                for c in columns
                if c.lower() in actual_set
            ]

            if filtered != columns:

                print(
                    f"Reconciled {table_name}: "
                    f"{len(columns)} source columns -> "
                    f"{len(filtered)} target columns"
                )

                registry[table_name] = filtered

        else:

            registry[table_name] = []

    with open(
        registry_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            registry,
            file,
            indent=4
        )


def generate(database):

    print()
    print("=====================================")
    print(f"BOOTSTRAP GENERATOR : {database.upper()}")
    print("=====================================")
    print()

    root = get_project_root()

    registry_path = (
        root
        / "metadata"
        / database
        / "schema_registry.json"
    )

    backup_path = (
        registry_path.with_suffix(".json.bak")
    )

    original_content = None

    if registry_path.exists():

        backup_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.copy2(
            registry_path,
            backup_path
        )

        original_content = registry_path.read_text(
            encoding="utf-8"
        )

    try:

        # --------------------------------------------------------
        # RECONCILE SCHEMA REGISTRY WITH TARGET DB
        #
        # Ensure auto-generated objects reference only columns
        # that actually exist in the target database.
        # --------------------------------------------------------

        _reconcile_schema_registry(database)

        # --------------------------------------------------------
        # PRE-GENERATION CLEANUP
        #
        # Remove stale generated files from a previous run so that
        # schema changes (table renames, additions, removals) are
        # reflected cleanly without leftover artefacts.
        # --------------------------------------------------------

        sql_out = root / "objects" / database / "generated"
        lq_out  = root / "liquibase" / database / "objects"
        master  = root / "liquibase" / database / "master_objects.xml"

        if sql_out.exists():
            shutil.rmtree(sql_out)

        if lq_out.exists():
            shutil.rmtree(lq_out)

        if master.exists():
            master.unlink()

        # --------------------------------------------------------
        # STEP 1 : Detect schema metadata
        # --------------------------------------------------------

        detector = ObjectDetector(database)
        detector.detect()

        # --------------------------------------------------------
        # STEP 2 : Generate SQL object files
        # --------------------------------------------------------

        if supports_object(database, "views"):
            generate_views(database)

        if supports_object(database, "functions"):
            generate_functions(database)

        if supports_object(database, "procedures"):
            generate_procedures(database)

        if supports_object(database, "triggers"):
            generate_triggers(database)

        if supports_object(database, "events"):
            generate_events(database)

        if supports_object(database, "indexes"):
            generate_indexes(database)

        # PostgreSQL-specific SQL generators
        if supports_object(database, "materialized_views"):
            generate_materialized_views(database)

        if supports_object(database, "extensions"):
            generate_extensions(database)

        # --------------------------------------------------------
        # STEP 3 : Generate Liquibase XML changesets
        # --------------------------------------------------------

        generate_liquibase_objects(database)

        # --------------------------------------------------------
        # STEP 4 : Generate master object changelog
        # --------------------------------------------------------

        generate_master_objects(database)

        print()
        print("=====================================")
        print("BOOTSTRAP GENERATION COMPLETE")
        print("=====================================")
        print()

    finally:

        if original_content is not None:

            registry_path.write_text(
                original_content,
                encoding="utf-8"
            )

            backup_path.unlink(
                missing_ok=True
            )


if __name__ == "__main__":

    if len(sys.argv) != 2:

        print("Usage : bootstrap_generator.py <database>")

        sys.exit(1)

    generate(sys.argv[1])
