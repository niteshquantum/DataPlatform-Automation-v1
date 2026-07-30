#!/usr/bin/env python

"""
Schema Detector Script

Scans the incoming/ folder for CSV and JSON files, extracts column names,
and maintains metadata in metadata/schema_registry.json
"""
import sys
import json
import logging
from pathlib import Path
import csv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_csv_headers(file_path):
    """
    Read CSV file and extract header row.
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        List of column names
    """
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            
            reader = csv.reader(f)
        
            headers = [
                h.replace('\ufeff', '').strip()
                for h in next(reader)
            ]
            logger.info(f"Extracted headers from {file_path.name}: {headers}")
            return headers
    except Exception as e:
        logger.error(f"Error reading CSV file {file_path}: {e}")
        return []


def get_json_keys(file_path):
    """
    Read JSON file and extract keys from first object.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        List of keys
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # Handle both single objects and arrays
            if isinstance(data, list):
                if data:
                    keys = list(data[0].keys()) if isinstance(data[0], dict) else []
                else:
                    keys = []
            elif isinstance(data, dict):
                keys = list(data.keys())
            else:
                keys = []
                
            logger.info(f"Extracted keys from {file_path.name}: {keys}")
            return keys
    except Exception as e:
        logger.error(f"Error reading JSON file {file_path}: {e}")
        return []


def update_schema_registry(table_name, columns, registry_path):
    """
    Update schema_registry.json with new columns.
    
    Args:
        table_name: Name of the table (filename without extension)
        columns: List of column names
        registry_path: Path to schema_registry.json
    """
    try:
        # Load existing schema registry
        if registry_path.exists():
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
        else:
            registry = {}
        
        # Add or update table
        if table_name in registry:
            # Merge columns, avoiding duplicates
            existing_columns = registry[table_name]
            new_columns = list(dict.fromkeys(existing_columns + columns))
            registry[table_name] = new_columns
            logger.info(f"Updated table '{table_name}' with new columns: {[col for col in new_columns if col not in existing_columns]}")
        else:
            registry[table_name] = columns
            logger.info(f"Created new table '{table_name}' with columns: {columns}")
        
        # Save updated registry
        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error updating schema registry: {e}")


def main():
    """
    Main function to scan incoming folder and update schema registry.
    """
    logger.info("Starting schema detection...")
    
    # Define paths
    project_root = Path(__file__).parent.parent

    # Database type from command line
    db_type = sys.argv[1].lower() if len(sys.argv) > 1 else "mongodb"

    # Database-specific folders
    incoming_dir = project_root / "incoming" / db_type

    registry_path = (
        project_root
        / "metadata"
        / db_type
        / "schema_registry.json"
    )

    logger.info(f"Database type: {db_type}")
    
    # Verify incoming directory exists
    if not incoming_dir.exists():
        logger.warning(f"Incoming directory not found: {incoming_dir}")
        return
    
    logger.info(f"Scanning incoming directory: {incoming_dir}")
    
    # Process CSV files
    csv_files = list(incoming_dir.glob("*.csv"))
    logger.info(f"Found {len(csv_files)} CSV file(s)")
    
    for csv_file in csv_files:
        table_name = (
            csv_file.stem
            .strip()
            .lower()
            .replace(' ', '_')
        )

        headers = get_csv_headers(csv_file)

        if headers:
            update_schema_registry(table_name, headers, registry_path)
    
    # Process JSON files
    json_files = list(incoming_dir.glob("*.json"))
    logger.info(f"Found {len(json_files)} JSON file(s)")
    
    for json_file in json_files:
        table_name = (
            json_file.stem
            .strip()
            .lower()
            .replace(' ', '_')
        )

        keys = get_json_keys(json_file)

        if keys:
            update_schema_registry(table_name, keys, registry_path)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        raise
