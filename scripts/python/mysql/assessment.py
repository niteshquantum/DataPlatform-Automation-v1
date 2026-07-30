"""MySQL information-schema assessment inventories."""

import argparse

from scripts.python.common.assessment import rows_as_dicts, run_selected, write_inventory
from scripts.python.mysql.setup.db_connection import get_connection

QUERIES = {
    "database": """
        SELECT
            schema_name AS database_name,
            default_character_set_name,
            default_collation_name
        FROM information_schema.schemata
        WHERE schema_name = DATABASE()
    """,

    "schema": """
        SELECT
            schema_name,
            default_character_set_name,
            default_collation_name
        FROM information_schema.schemata
        WHERE schema_name = DATABASE()
    """,

    "table": """
        SELECT
            table_schema AS schema_name,
            table_name,
            table_type,
            engine,
            table_rows
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """,

    "view": """
        SELECT
            table_schema AS schema_name,
            table_name AS view_name,
            definer,
            security_type
        FROM information_schema.views
        WHERE table_schema = DATABASE()
        ORDER BY table_name
    """,

    "procedure": """
        SELECT
            routine_schema AS schema_name,
            routine_name AS procedure_name,
            created,
            last_altered
        FROM information_schema.routines
        WHERE routine_schema = DATABASE()
          AND routine_type = 'PROCEDURE'
        ORDER BY routine_name
    """,

    "function": """
        SELECT
            routine_schema AS schema_name,
            routine_name AS function_name,
            data_type AS return_type,
            created,
            last_altered
        FROM information_schema.routines
        WHERE routine_schema = DATABASE()
          AND routine_type = 'FUNCTION'
        ORDER BY routine_name
    """,

    "trigger": """
        SELECT
            trigger_schema AS schema_name,
            trigger_name,
            event_manipulation,
            event_object_table,
            action_timing
        FROM information_schema.triggers
        WHERE trigger_schema = DATABASE()
        ORDER BY trigger_name
    """,

    "event": """
        SELECT
            event_schema AS schema_name,
            event_name,
            status,
            event_type,
            interval_value,
            interval_field
        FROM information_schema.events
        WHERE event_schema = DATABASE()
        ORDER BY event_name
    """,

    "index": """
        SELECT
            table_schema AS schema_name,
            table_name,
            index_name,
            non_unique,
            seq_in_index,
            column_name,
            index_type
        FROM information_schema.statistics
        WHERE table_schema = DATABASE()
        ORDER BY
            table_name,
            index_name,
            seq_in_index
    """
}

def run(inventory):
    connection = get_connection(); cursor = connection.cursor()
    try:
        cursor.execute(QUERIES[inventory])
        return write_inventory("mysql", inventory, rows_as_dicts(cursor))
    finally:
        cursor.close(); connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a MySQL assessment inventory")
    parser.add_argument("inventory", choices=[*QUERIES, "all"])
    run_selected(run, list(QUERIES), parser.parse_args().inventory)
