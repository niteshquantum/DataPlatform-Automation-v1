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
        with open(file_path, "r", encoding="utf-8-sig") as f:
            
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
def detect_schema_changes(existing_columns, current_columns):
    """
    Compare existing and current schema.
    Returns NEW, CHANGED, DELETED or UNCHANGED.
    """

    existing = {c.lower().strip() for c in existing_columns}
    current = {c.lower().strip() for c in current_columns}

    added = list(current - existing)
    deleted = list(existing - current)

    if not existing_columns:
        return {
            "status": "NEW",
            "added_columns": current_columns,
            "deleted_columns": []
        }

    if added:
        return {
            "status": "CHANGED",
            "added_columns": added,
            "deleted_columns": deleted
        }

    if deleted:
        return {
            "status": "DELETED",
            "added_columns": [],
            "deleted_columns": deleted
        }

    return {
        "status": "UNCHANGED",
        "added_columns": [],
        "deleted_columns": []
    }
def update_schema_registry(table_name, columns, registry_path):
    """
    Update schema_registry.json with new columns.
    """
    try:
        if registry_path.exists():
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
        else:
            registry = {}

        # Normalize incoming columns
        columns = [
            col.replace('\ufeff', '').strip()
            for col in columns
        ]

        if table_name in registry:

            existing_columns = [
                col.replace('\ufeff', '').strip()
                for col in registry[table_name]
            ]

            new_columns = []
            seen = set()

            for col in existing_columns + columns:
                key = col.lower()

                if key not in seen:
                    seen.add(key)
                    new_columns.append(col)

            added_columns = [
                col for col in new_columns
                if col not in existing_columns
            ]

            registry[table_name] = new_columns
            
            

            logger.info(
                f"Updated table '{table_name}' "
                f"with new columns: {added_columns}"
            )

        else:
            registry[table_name] = columns

            logger.info(
                f"Created new table '{table_name}' "
                f"with columns: {columns}"
            )

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
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)
        cdc_status = {"tables": {}}
        cdc_path = project_root / "metadata" / db_type / "cdc_status.json"
        cdc_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cdc_path, "w", encoding="utf-8") as f:
            json.dump(cdc_status, f, indent=4)
        logger.info(f"Initialized empty schema registry at {registry_path}")
        logger.info(f"CDC metadata written to {cdc_path}")
        return
    
    logger.info(f"Scanning incoming directory: {incoming_dir}")
    cdc_status = {
    "tables": {}
    }
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

            existing_columns = []

            if registry_path.exists():
                with open(registry_path, "r", encoding="utf-8") as f:
                    registry = json.load(f)

                existing_columns = registry.get(table_name, [])

                result = detect_schema_changes(existing_columns, headers)

                logger.info(
                    f"CDC Status [{table_name}] : {result['status']}"
                )

                cdc_status["tables"][table_name] = result

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

            existing_columns = []

            if registry_path.exists():
                with open(registry_path, "r", encoding="utf-8") as f:
                    registry = json.load(f)

                existing_columns = registry.get(table_name, [])

            result = detect_schema_changes(existing_columns, keys)

            logger.info(
                f"CDC Status [{table_name}] : {result['status']}"
            )
            cdc_status["tables"][table_name] = result
        update_schema_registry(table_name, keys, registry_path)
    cdc_path = (
        project_root
        / "metadata"
        / db_type
        / "cdc_status.json"
    )

    with open(cdc_path, "w", encoding="utf-8") as f:
        json.dump(cdc_status, f, indent=4)

    logger.info(f"CDC metadata written to {cdc_path}")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        raise