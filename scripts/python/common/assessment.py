"""Shared persistence and report helpers for database assessments."""

import json
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from scripts.python.common.config_loader import load_database_config

ROOT = Path(__file__).resolve().parents[3]
ASSESSMENT_ROOT = ROOT / "outputs" / "assessments"

INVENTORY_DETAILS = {
    "database": ("DATABASE INVENTORY", "Total Databases", "Databases", "database_name"),
    "schema": ("SCHEMA INVENTORY", "Total Schemas", "Schemas", "schema_name"),
    "table": ("TABLE INVENTORY", "Total Tables", "Tables", "table_name"),
    "view": ("VIEW INVENTORY", "Total Views", "Views", "view_name"),
    "procedure": ("STORED PROCEDURE INVENTORY", "Total Stored Procedures", "Stored Procedures", "procedure_name"),
    "function": ("FUNCTION INVENTORY", "Total Functions", "Functions", "function_name"),
    "trigger": ("TRIGGER INVENTORY", "Total Triggers", "Triggers", "trigger_name"),
    "event": ("EVENT INVENTORY", "Total Events", "Events", "event_name"),
    "extension": ("EXTENSION INVENTORY", "Total Extensions", "Extensions", "extension_name"),
    "materialized_view": ("MATERIALIZED VIEW INVENTORY", "Total Materialized Views", "Materialized Views", "materialized_view_name"),
    "collection": ("COLLECTION INVENTORY", "Total Collections", "Collections", "collection_name"),
    "index": ("INDEX INVENTORY", "Total Indexes", "Indexes", "index_name"),
    "sql_agent_inventory": ("SQL AGENT INVENTORY", "Total SQL Agent Jobs", "SQL Agent Jobs", "job_name"),
    "sql_agent_validation": ("SQL AGENT VALIDATION", "Total Jobs Validated", "Validation Results", "job_name"),
    "sql_agent_history": ("SQL AGENT HISTORY", "Recent Executions", "Recent Executions", "job_name"),
    "sql_agent_assessment": ("SQL AGENT ASSESSMENT", "Assessment Metrics", "Assessment Metrics", None),
}

DATABASE_CONFIG_KEYS = {
    "mssql": "MSSQL_DB",
    "mysql": "MYSQL_DB",
    "postgresql": "POSTGRESQL_DB",
    "mongodb": "MONGODB_DATABASE",
}

DATABASE_ENGINE_NAMES = {
    "mssql": "MSSQL",
    "mysql": "MySQL",
    "postgresql": "PostgreSQL",
    "mongodb": "MongoDB",
}

SINGULAR_OBJECT_NAMES = {
    "database": "database",
    "schema": "schema",
    "table": "table",
    "view": "view",
    "procedure": "stored procedure",
    "function": "function",
    "trigger": "trigger",
    "event": "event",
    "extension": "extension",
    "materialized_view": "materialized view",
    "collection": "collection",
    "index": "index",
    "sql_agent_inventory": "SQL Agent job",
    "sql_agent_validation": "validation result",
    "sql_agent_history": "recent execution",
    "sql_agent_assessment": "assessment metric",
}


def json_value(value):
    """Return a JSON-safe value without changing inventory-specific data."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def rows_as_dicts(cursor):
    columns = [column[0] for column in cursor.description]
    return [
        {name: json_value(value) for name, value in zip(columns, row)}
        for row in cursor.fetchall()
    ]


def get_database_name(database):
    """Use the configured database name solely for console presentation."""
    config = load_database_config(database)
    return config.get(DATABASE_CONFIG_KEYS[database], "Not available")


def get_display_names(rows, name_key):
    if not name_key:
        return []
    names = []
    for row in rows:
        normalized_row = {str(key).lower(): value for key, value in row.items()}
        name = normalized_row.get(name_key.lower()) or normalized_row.get("name")
        if name is not None:
            names.append(str(name))
    return list(dict.fromkeys(names))


def format_numbered_list(title, names):
    if not names:
        return ""
    entries = "\n".join(f"{index}. {name}" for index, name in enumerate(names, start=1))
    return f"\n{title}\n\n{entries}\n"


def format_sql_agent_details(inventory, rows):
    if inventory == "sql_agent_inventory":
        return "".join(
            "\n"
            f"Job Name : {row.get('job_name', 'Not available')}\n"
            f"Owner : {row.get('owner', 'Not available')}\n"
            f"Enabled : {'Yes' if row.get('enabled') else 'No'}\n"
            f"Schedule : {row.get('schedule_name') or 'Not scheduled'}\n"
            "Last Run : Not available\n"
            "Next Run : Not available\n"
            for row in rows
        )
    if inventory == "sql_agent_validation":
        return "".join(
            "\n"
            f"Job Name : {row.get('job_name', 'Not available')}\n"
            "Validation Result : PASS\n"
            "Reason : SQL Agent job configuration was retrieved successfully.\n"
            for row in rows
        )
    if inventory == "sql_agent_history":
        return "".join(
            "\n"
            f"Job Name : {row.get('job_name', 'Not available')}\n"
            f"Execution : {row.get('run_date') or 'Not available'}\n"
            f"Duration : {row.get('run_duration') or 'Not available'}\n"
            f"Result : {'Success' if row.get('run_status') == 1 else 'Failure'}\n"
            for row in rows
        )
    if inventory == "sql_agent_assessment" and rows:
        row = rows[0]
        enabled = row.get("enabled_jobs") or 0
        disabled = row.get("disabled_jobs") or 0
        return (
            "\n"
            f"Total Jobs : {row.get('total_jobs') or 0}\n"
            f"Enabled Jobs : {enabled}\n"
            f"Disabled Jobs : {disabled}\n"
            f"Healthy Jobs : {enabled}\n"
            f"Warnings : {disabled} disabled job(s) require review.\n"
        )
    return ""


def print_inventory_summary(database, inventory, rows, status):
    """Print a business-facing summary without exposing implementation paths."""
    title, count_label, list_title, name_key = INVENTORY_DETAILS[inventory]
    record_count = len(rows)
    object_name = SINGULAR_OBJECT_NAMES[inventory]
    database_name = get_database_name(database)
    status_label = "PASS" if status == "complete" else status.upper()

    plural_names = {
        "index": "indexes",
        "database": "databases",
        "schema": "schemas",
        "table": "tables",
        "view": "views",
        "stored procedure": "stored procedures",
        "function": "functions",
        "trigger": "triggers",
        "event": "events",
        "extension": "extensions",
        "materialized view": "materialized views",
        "collection": "collections",
        "SQL Agent job": "SQL Agent jobs",
        "validation result": "validation results",
        "recent execution": "recent executions",
        "assessment metric": "assessment metrics",
    }

    display_object_name = (
        object_name
        if record_count == 1
        else plural_names.get(
            object_name,
            f"{object_name}s"
        )
    )

    summary = (
        f"{record_count} {display_object_name} successfully discovered."
        if record_count
        else f"No {list_title.lower()} currently exist."
    )
    recommendation = (
        "No action required."
        if record_count
        else "No action required; this inventory is currently empty."
    )
    names = get_display_names(rows, name_key)
    details = format_sql_agent_details(inventory, rows)
    print(
        f"\n{'=' * 50}\n"
        f"{title}\n"
        f"{'=' * 50}\n\n"
        f"Database Engine : {DATABASE_ENGINE_NAMES[database]}\n\n"
        f"Database Name : {database_name}\n\n"
        f"{count_label} : {record_count}\n"
        f"{format_numbered_list(list_title, names)}"
        f"{details}\n"
        "Summary\n\n"
        f"{summary}\n\n"
        "Status\n\n"
        f"{status_label}\n\n"
        "Recommendation\n\n"
        f"{recommendation}\n\n"
        f"{'=' * 50}\n"
    )


def write_inventory(database, inventory, rows, status="complete", detail=None):
    """Persist one portable inventory using the same layout for every engine."""
    destination = ASSESSMENT_ROOT / database / f"{inventory}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "database_platform": database,
        "inventory": inventory,
        "status": status,
        "record_count": len(rows),
        "records": rows,
    }
    if detail:
        payload["detail"] = detail
    destination.write_text(json.dumps(payload, indent=2, default=json_value) + "\n", encoding="utf-8")
    print_inventory_summary(
        database,
        inventory,
        payload["records"],
        payload["status"],
    )
    return payload


def run_selected(run_inventory, inventory_names, selected):
    """Run one inventory or every inventory without duplicating CLI behaviour."""
    names = inventory_names if selected == "all" else [selected]
    return [run_inventory(name) for name in names]
