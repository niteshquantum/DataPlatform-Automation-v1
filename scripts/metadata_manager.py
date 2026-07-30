#!/usr/bin/env python
"""
Metadata Manager Script

Reads config/metadata_schema.json, registers new tables and columns,
and maintains audit history.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_metadata_schema(schema_path):
    """
    Load metadata schema from JSON file.
    """
    try:
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
                logger.info(f"Loaded metadata schema: {len(schema.get('tables', {}))} table(s)")
                return schema
        else:
            logger.info(f"Metadata schema not found, initializing new schema: {schema_path}")
            return {"tables": {}, "audit_history": []}
    except Exception as e:
        logger.error(f"Error loading metadata schema: {e}")
        return {"tables": {}, "audit_history": []}


def save_metadata_schema(schema_path, schema):
    """
    Save metadata schema to JSON file.
    """
    try:
        schema_path.parent.mkdir(parents=True, exist_ok=True)
        with open(schema_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
            logger.info(f"Saved metadata schema: {schema_path}")
    except Exception as e:
        logger.error(f"Error saving metadata schema: {e}")


def register_table(schema, table_name):
    """
    Register a table in the metadata schema.
    """
    tables = schema.setdefault("tables", {})
    if table_name not in tables:
        tables[table_name] = {"columns": {}}
        logger.info(f"Registered new table: {table_name}")
        return True
    logger.info(f"Table already registered: {table_name}")
    return False


def register_column(schema, table_name, column_name):
    """
    Register a column for a table in the metadata schema.
    """
    tables = schema.setdefault("tables", {})
    table = tables.setdefault(table_name, {"columns": {}})
    columns = table.setdefault("columns", {})
    if column_name not in columns:
        columns[column_name] = {"storage_type": "VARCHAR(255)"}
        logger.info(f"Registered column '{column_name}' for table '{table_name}'")
        return True
    logger.info(f"Column '{column_name}' already exists for table '{table_name}'")
    return False


def add_audit_entry(schema, table_name, column_name, action):
    """
    Add an audit entry to metadata schema.
    """
    entry = {
        "timestamp": datetime.now().isoformat(),
        "table_name": table_name,
        "column_name": column_name,
        "action": action
    }
    audit_history = schema.setdefault("audit_history", [])
    audit_history.append(entry)
    logger.info(f"Audit entry added: {action} {table_name}.{column_name}")


def main():
    """
    Main function to register metadata changes.
    """
    logger.info("Starting metadata manager...")

    project_root = Path(__file__).parent.parent
    schema_path = project_root / "config" / "metadata_schema.json"
    
    schema = load_metadata_schema(schema_path)

    # Example usage placeholder: register table/columns here.
    # The script can be extended to accept arguments or process incoming metadata.
    
    # Example operations (no-op if already registered):
    table_name = "customers"
    columns = ["CustomerID", "FirstName", "LastName", "City"]

    table_added = register_table(schema, table_name)
    if table_added:
        add_audit_entry(schema, table_name, "", "ADD_TABLE")

    for column_name in columns:
        column_added = register_column(schema, table_name, column_name)
        if column_added:
            add_audit_entry(schema, table_name, column_name, "ADD_COLUMN")

    save_metadata_schema(schema_path, schema)
    logger.info("Metadata manager completed")


if __name__ == "__main__":
    main()