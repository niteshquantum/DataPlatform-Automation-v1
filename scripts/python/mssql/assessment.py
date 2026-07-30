"""MSSQL catalogue assessment inventories."""

import argparse

from scripts.python.common.assessment import rows_as_dicts, run_selected, write_inventory
from scripts.python.mssql.setup.db_connection import get_connection
from scripts.python.mssql.load.sql_agent import get_records

QUERIES = {
    "database": "SELECT name, compatibility_level, recovery_model_desc, collation_name FROM sys.databases WHERE name = DB_NAME()",
    "schema": "SELECT name AS schema_name, principal_id FROM sys.schemas ORDER BY name",
    "table": "SELECT s.name AS schema_name, t.name AS table_name, t.create_date, t.modify_date FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id ORDER BY s.name,t.name",
    "view": "SELECT s.name AS schema_name, v.name AS view_name, v.create_date, v.modify_date FROM sys.views v JOIN sys.schemas s ON s.schema_id=v.schema_id ORDER BY s.name,v.name",
    "procedure": "SELECT s.name AS schema_name, p.name AS procedure_name, p.create_date, p.modify_date FROM sys.procedures p JOIN sys.schemas s ON s.schema_id=p.schema_id ORDER BY s.name,p.name",
    "function": "SELECT s.name AS schema_name, o.name AS function_name, o.type_desc, o.create_date, o.modify_date FROM sys.objects o JOIN sys.schemas s ON s.schema_id=o.schema_id WHERE o.type IN ('FN','IF','TF','FS','FT') ORDER BY s.name,o.name",
    "trigger": "SELECT s.name AS schema_name, t.name AS trigger_name, OBJECT_SCHEMA_NAME(t.parent_id) AS parent_schema, OBJECT_NAME(t.parent_id) AS parent_name, t.is_disabled FROM sys.triggers t JOIN sys.objects o ON o.object_id=t.object_id JOIN sys.schemas s ON s.schema_id=o.schema_id WHERE t.parent_class=1 ORDER BY s.name,t.name",
    "index": "SELECT s.name AS schema_name, tb.name AS table_name, i.name AS index_name, i.type_desc, i.is_unique, i.is_primary_key FROM sys.indexes i JOIN sys.tables tb ON tb.object_id=i.object_id JOIN sys.schemas s ON s.schema_id=tb.schema_id WHERE i.index_id > 0 AND tb.is_ms_shipped=0 ORDER BY s.name, tb.name, i.name",
}


def fetch(cursor, query):
    cursor.execute(query)
    return rows_as_dicts(cursor)


def run(inventory):
    if inventory.startswith("sql_agent_"):
        return write_inventory(
            "mssql",
            inventory,
            get_records(inventory.removeprefix("sql_agent_")),
        )

    connection = get_connection()
    try:
        cursor = connection.cursor()
        try:
            rows = fetch(cursor, QUERIES[inventory])
            return write_inventory("mssql", inventory, rows)
        finally:
            cursor.close()
    finally:
        connection.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run an MSSQL assessment inventory")
    sql_agent_inventories = ["sql_agent_inventory", "sql_agent_validation", "sql_agent_history", "sql_agent_assessment"]
    parser.add_argument("inventory", choices=[*QUERIES, *sql_agent_inventories, "all"])
    run_selected(run, [*QUERIES, *sql_agent_inventories], parser.parse_args().inventory)
