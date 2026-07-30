"""PostgreSQL catalogue assessment inventories."""

import argparse

from scripts.python.common.assessment import rows_as_dicts, run_selected, write_inventory
from scripts.python.postgresql.setup.db_connection import get_connection

QUERIES = {
    "database": "SELECT datname AS database_name, pg_encoding_to_char(encoding) AS encoding, datcollate, datctype FROM pg_database WHERE datname=current_database()",
    "schema": "SELECT schema_name, schema_owner FROM information_schema.schemata ORDER BY schema_name",
    "table": "SELECT table_schema AS schema_name, table_name, table_type FROM information_schema.tables WHERE table_schema NOT IN ('pg_catalog','information_schema') AND table_type='BASE TABLE' ORDER BY table_schema,table_name",
    "view": "SELECT table_schema AS schema_name, table_name AS view_name FROM information_schema.views WHERE table_schema NOT IN ('pg_catalog','information_schema') ORDER BY table_schema,table_name",
    "procedure": "SELECT routine_schema AS schema_name, routine_name AS procedure_name, data_type AS return_type FROM information_schema.routines WHERE routine_type='PROCEDURE' AND routine_schema NOT IN ('pg_catalog','information_schema') ORDER BY routine_schema,routine_name",
    "function": "SELECT routine_schema AS schema_name, routine_name AS function_name, data_type AS return_type FROM information_schema.routines WHERE routine_type='FUNCTION' AND routine_schema NOT IN ('pg_catalog','information_schema') ORDER BY routine_schema,routine_name",
    "trigger": "SELECT trigger_schema AS schema_name, trigger_name, event_manipulation, event_object_table, action_timing FROM information_schema.triggers WHERE trigger_schema NOT IN ('pg_catalog','information_schema') ORDER BY trigger_schema,trigger_name",
    "extension": "SELECT extname AS extension_name, extversion AS extension_version FROM pg_extension ORDER BY extname",
    "materialized_view": "SELECT schemaname AS schema_name, matviewname AS materialized_view_name, ispopulated FROM pg_matviews WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY schemaname,matviewname",
    "index": "SELECT schemaname AS schema_name, tablename AS table_name, indexname AS index_name, indexdef FROM pg_indexes WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY schemaname, tablename, indexname",
}


def run(inventory):
    connection = get_connection(); cursor = connection.cursor()
    try:
        cursor.execute(QUERIES[inventory])
        return write_inventory("postgresql", inventory, rows_as_dicts(cursor))
    finally:
        cursor.close(); connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a PostgreSQL assessment inventory")
    parser.add_argument("inventory", choices=[*QUERIES, "all"])
    run_selected(run, list(QUERIES), parser.parse_args().inventory)
