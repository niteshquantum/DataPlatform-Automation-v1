#!/usr/bin/env python
"""
Liquibase Generator Script

Reads metadata/schema_changes.json and generates Liquibase XML files
for creating new tables and altering existing tables.
"""

import json
import logging
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_schema_changes(changes_path):
    """
    Load schema_changes.json.
    
    Args:
        changes_path: Path to schema_changes.json
        
    Returns:
        Dictionary with schema changes
    """
    try:
        if changes_path.exists():
            with open(changes_path, 'r', encoding='utf-8') as f:
                changes = json.load(f)
                logger.info(f"Loaded schema changes: {len(changes)} table(s)")
                return changes
        else:
            logger.warning(f"Schema changes file not found: {changes_path}")
            return {}
    except Exception as e:
        logger.error(f"Error loading schema changes: {e}")
        return {}


def generate_unique_id(table_name):
    """
    Generate unique changeSet id using timestamp and table name.
    
    Args:
        table_name: Name of the table
        
    Returns:
        Unique changeSet id
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{timestamp}-{table_name}"


def create_xml_root():
    """
    Create root element for Liquibase databaseChangeLog.
    
    Returns:
        Root Element
    """
    root = Element('databaseChangeLog')
    root.set('xmlns', 'http://www.liquibase.org/xml/ns/dbchangelog')
    root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    root.set('xsi:schemaLocation', 
             'http://www.liquibase.org/xml/ns/dbchangelog http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-3.8.xsd')
    return root


def create_table_xml(table_name, columns):
    """
    Generate XML for CREATE TABLE statement.
    
    Args:
        table_name: Name of the table
        columns: List of column names
        
    Returns:
        ElementTree
    """
    root = create_xml_root()
    changeset = SubElement(root, 'changeSet')
    changeset.set('id', generate_unique_id(f"{table_name}-create"))
    changeset.set('author', 'auto-generated')
    
    create_table = SubElement(changeset, 'createTable')
    create_table.set('tableName', table_name)
    
    # Add columns
    for i, column in enumerate(columns):
        column_elem = SubElement(create_table, 'column')
        column_elem.set('name', column)
        
        # Infer type based on column name (simple heuristic)
        if column.lower() in ['id', 'customerid', 'userid', 'orderid', 'productid', 'sellerid']:
            column_elem.set('type', 'INT')
            # Add primary key constraint for ID columns
            constraints = SubElement(column_elem, 'constraints')
            constraints.set('primaryKey', 'true')
            constraints.set('nullable', 'false')
        elif column.lower() in ['email', 'firstname', 'lastname', 'city', 'state', 'name']:
            column_elem.set('type', 'VARCHAR(255)')
        elif column.lower() in ['joindate', 'createddate', 'modifieddate']:
            column_elem.set('type', 'DATETIME')
        elif column.lower() in ['salary', 'price', 'amount', 'total']:
            column_elem.set('type', 'DECIMAL(10,2)')
        elif column.lower() in ['phone']:
            column_elem.set('type', 'VARCHAR(20)')
        else:
            # Default type
            column_elem.set('type', 'VARCHAR(255)')
    
    return ElementTree(root)


def alter_table_xml(table_name, new_columns):
    """
    Generate XML for ALTER TABLE statement (add columns).
    
    Args:
        table_name: Name of the table
        new_columns: List of new column names
        
    Returns:
        ElementTree
    """
    root = create_xml_root()
    changeset = SubElement(root, 'changeSet')
    changeset.set('id', generate_unique_id(f"{table_name}-alter"))
    changeset.set('author', 'auto-generated')
    
    add_column = SubElement(changeset, 'addColumn')
    add_column.set('tableName', table_name)
    
    # Add new columns
    for column in new_columns:
        column_elem = SubElement(add_column, 'column')
        column_elem.set('name', column)
        
        # Infer type based on column name (simple heuristic)
        if column.lower() in ['email']:
            column_elem.set('type', 'VARCHAR(255)')
        elif column.lower() in ['phone']:
            column_elem.set('type', 'VARCHAR(20)')
        elif column.lower() in ['salary', 'price', 'amount', 'total']:
            column_elem.set('type', 'DECIMAL(10,2)')
        else:
            # Default type
            column_elem.set('type', 'VARCHAR(255)')
    
    return ElementTree(root)


def save_xml(xml_tree, output_path):
    """
    Save XML tree to file with proper formatting.
    
    Args:
        xml_tree: ElementTree to save
        output_path: Path to output XML file
    """
    try:
        # Add XML declaration
        xml_tree.write(output_path, encoding='utf-8', xml_declaration=True)
        logger.info(f"Generated XML file: {output_path.name}")
    except Exception as e:
        logger.error(f"Error saving XML file {output_path}: {e}")


def main():
    """
    Main function to generate Liquibase XML files from schema changes.
    """
    logger.info("Starting Liquibase XML generation...")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    changes_path = project_root / "metadata" / "schema_changes.json"
    output_dir = project_root / "liquibase" / "generated"
    
    # Create output directory if needed
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using output directory: {output_dir}")
    
    # Load schema changes
    schema_changes = load_schema_changes(changes_path)
    
    if not schema_changes:
        logger.warning("No schema changes found")
        return
    
    # Process each table
    for table_name, changes in schema_changes.items():
        logger.info(f"Processing table: {table_name}")
        
        new_columns = changes.get("new_columns", [])
        existing_columns = changes.get("existing_columns", [])
        
        # Skip if no changes
        if not new_columns:
            logger.info(f"  Skipping {table_name}: no new columns")
            continue
        
        # Case 1: New table (no existing columns)
        if not existing_columns:
            output_file = output_dir / f"{table_name}_create.xml"
            
            # Don't overwrite existing files
            if output_file.exists():
                logger.warning(f"  Skipping {output_file.name}: file already exists")
            else:
                all_columns = new_columns
                xml_tree = create_table_xml(table_name, all_columns)
                save_xml(xml_tree, output_file)
                logger.info(f"  Created CREATE TABLE for {table_name}: {len(all_columns)} column(s)")
        
        # Case 2: Existing table with new columns
        else:
            output_file = output_dir / f"{table_name}_alter.xml"
            
            # Don't overwrite existing files
            if output_file.exists():
                logger.warning(f"  Skipping {output_file.name}: file already exists")
            else:
                xml_tree = alter_table_xml(table_name, new_columns)
                save_xml(xml_tree, output_file)
                logger.info(f"  Created ALTER TABLE for {table_name}: {len(new_columns)} new column(s)")
    
    logger.info("Liquibase XML generation completed successfully")


if __name__ == "__main__":
    main()