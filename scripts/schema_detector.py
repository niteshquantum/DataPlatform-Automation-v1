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

COMMON_MODULE_DIR = Path(__file__).resolve().parent / "python" / "common"
if str(COMMON_MODULE_DIR) not in sys.path:
    sys.path.insert(0, str(COMMON_MODULE_DIR))

from column_mapper import map_columns, map_table_name

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger("column_mapper").setLevel(logging.WARNING)


def log_file_details(file_path, table_name, column_count):
    """Log a concise overview before processing a source file."""
    logger.info(
        "\n==================================================\n"
        f"Processing File : {file_path.name}\n"
        f"Table Name      : {table_name}\n"
        f"Columns Found   : {column_count}\n"
        "=================================================="
    )


def log_column_mapping(columns, mapped_columns):
    """Log each source-to-standardized column mapping once."""
    logger.info("\nColumn Mapping\n------------------------------------------")
    for column, mapped_column in zip(columns, mapped_columns):
        logger.info(f"{column:<15} -> {mapped_column}")
    logger.info("------------------------------------------")


def log_schema_status(result):
    """Log schema-change details in a readable format."""
    status = result["status"]
    if status == "UNCHANGED":
        logger.info(f"Schema Status : {status}")
        logger.info("No schema changes detected.")
        return

    logger.info("\nSchema Comparison\n------------------------------------------")
    logger.info(f"Schema Status : {status}")

    if status == "DELETED":
        logger.info("\nTarget columns missing in current dataset:")
        for column in result["deleted_columns"]:
            logger.info(f" - {column}")
        logger.info(
            "\nReason:\n"
            "These columns existed in the previous schema but are not present "
            "in the current source dataset."
        )
    else:
        if result["added_columns"]:
            logger.info("\nNew Columns:")
            for column in result["added_columns"]:
                logger.info(f" + {column}")
        if result["deleted_columns"]:
            logger.info("\nDeleted Columns:")
            for column in result["deleted_columns"]:
                logger.info(f" - {column}")

    logger.info("------------------------------------------")


def log_mapping_summary(summary):
    """Log totals for all processed source files."""
    logger.info(
        "\n==================================================\n"
        "COLUMN MAPPING SUMMARY\n"
        "==================================================\n"
        f"Files Processed : {summary['files_processed']}\n"
        f"CSV Files       : {summary['csv_files']}\n"
        f"JSON Files      : {summary['json_files']}\n"
        "\n"
        f"Total Columns       : {summary['total_columns']}\n"
        f"Mapped Successfully : {summary['mapped_columns']}\n"
        f"Unmapped Columns    : {summary['unmapped_columns']}\n"
        "\n"
        "Schema Status\n"
        "-------------\n"
        f"New Tables          : {summary['new']}\n"
        f"Changed Tables      : {summary['changed']}\n"
        f"Deleted Tables      : {summary['deleted']}\n"
        f"Unchanged Tables    : {summary['unchanged']}\n"
        "=================================================="
    )


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
                
            return keys
    except Exception as e:
        logger.error(f"Error reading JSON file {file_path}: {e}")
        return []
def _normalize_column_name(column):
    """Normalize a column name for safe compare operations."""
    return str(column).strip().lower().replace("\ufeff", "")


def _detect_renames(existing_columns, current_columns):
    """Return a conservative rename map for one-to-one column renames."""
    existing_norm = [_normalize_column_name(col) for col in existing_columns]
    current_norm = [_normalize_column_name(col) for col in current_columns]

    deleted = [col for col in existing_columns if _normalize_column_name(col) not in current_norm]
    added = [col for col in current_columns if _normalize_column_name(col) not in existing_norm]

    if len(deleted) != 1 or len(added) != 1:
        return {}

    old_name = deleted[0]
    new_name = added[0]
    old_key = _normalize_column_name(old_name)
    new_key = _normalize_column_name(new_name)

    if old_key == new_key:
        return {old_name: new_name}

    old_tokens = [token for token in old_key.split("_") if token]
    new_tokens = [token for token in new_key.split("_") if token]

    common_prefix = 0
    while common_prefix < min(len(old_tokens), len(new_tokens)) and old_tokens[common_prefix] == new_tokens[common_prefix]:
        common_prefix += 1

    common_suffix = 0
    while common_suffix < min(len(old_tokens) - common_prefix, len(new_tokens) - common_prefix) and old_tokens[-1 - common_suffix] == new_tokens[-1 - common_suffix]:
        common_suffix += 1

    old_core = old_tokens[common_prefix:len(old_tokens) - common_suffix]
    new_core = new_tokens[common_prefix:len(new_tokens) - common_suffix]

    if len(old_core) == 0 and len(new_core) == 1:
        return {old_name: new_name}
    if len(new_core) == 0 and len(old_core) == 1:
        return {old_name: new_name}
    if old_core == [] or new_core == []:
        return {}
    if old_core == new_core:
        return {old_name: new_name}
    if len(old_core) == 1 and len(new_core) == 1 and old_core[0] != new_core[0]:
        return {old_name: new_name}
    if len(old_core) <= 2 and len(new_core) <= 2 and set(old_core) == set(new_core):
        return {old_name: new_name}

    return {}


def detect_schema_changes(existing_columns, current_columns):
    """
    Compare existing and current schema.
    Returns NEW, CHANGED, DELETED, RENAMED, or UNCHANGED.
    """
    existing = [_normalize_column_name(c) for c in existing_columns]
    current = [_normalize_column_name(c) for c in current_columns]

    added = [col for col in current_columns if _normalize_column_name(col) not in existing]
    deleted = [col for col in existing_columns if _normalize_column_name(col) not in current]

    if not existing_columns:
        return {
            "status": "NEW",
            "added_columns": list(current_columns),
            "deleted_columns": [],
            "renamed_columns": {},
            "datatype_changes": [],
        }

    renamed = _detect_renames(existing_columns, current_columns)
    if renamed:
        return {
            "status": "RENAMED",
            "added_columns": list(added),
            "deleted_columns": list(deleted),
            "renamed_columns": renamed,
            "datatype_changes": [],
        }

    if added:
        return {
            "status": "CHANGED",
            "added_columns": list(added),
            "deleted_columns": list(deleted),
            "renamed_columns": {},
            "datatype_changes": [],
        }

    if deleted:
        return {
            "status": "DELETED",
            "added_columns": [],
            "deleted_columns": list(deleted),
            "renamed_columns": {},
            "datatype_changes": [],
        }

    return {
        "status": "UNCHANGED",
        "added_columns": [],
        "deleted_columns": [],
        "renamed_columns": {},
        "datatype_changes": [],
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
            
            

        else:
            registry[table_name] = columns

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
    summary = {
        "files_processed": 0,
        "csv_files": 0,
        "json_files": 0,
        "total_columns": 0,
        "mapped_columns": 0,
        "unmapped_columns": 0,
        "changed": 0,
        "new": 0,
        "deleted": 0,
        "unchanged": 0,
    }

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
        log_mapping_summary(summary)
        return
    
    logger.info(f"Scanning incoming directory: {incoming_dir}")
    cdc_status = {
    "tables": {}
    }
    # Process CSV files
    csv_files = list(incoming_dir.glob("*.csv"))
    logger.info(f"Found {len(csv_files)} CSV file(s)")
    
    for csv_file in csv_files:
        summary["files_processed"] += 1
        summary["csv_files"] += 1
        table_name = map_table_name(csv_file.stem)

        headers = get_csv_headers(csv_file)
        log_file_details(csv_file, table_name, len(headers))

        if headers:
            mapped_headers = map_columns(headers)
            summary["total_columns"] += len(headers)
            summary["mapped_columns"] += len(mapped_headers)
            summary["unmapped_columns"] += max(len(headers) - len(mapped_headers), 0)
            log_column_mapping(headers, mapped_headers)

            existing_columns = []

            if registry_path.exists():
                with open(registry_path, "r", encoding="utf-8") as f:
                    registry = json.load(f)

                existing_columns = registry.get(table_name, [])

                cdc_status["tables"][table_name] = detect_schema_changes(
                    existing_columns, mapped_headers
                )

            result = detect_schema_changes(existing_columns, mapped_headers)
            log_schema_status(result)
            summary[result["status"].lower()] += 1

            update_schema_registry(table_name, mapped_headers, registry_path)
            logger.info("Schema Registry Updated Successfully.")
    
    # Process JSON files
    json_files = list(incoming_dir.glob("*.json"))
    logger.info(f"Found {len(json_files)} JSON file(s)")
    
    for json_file in json_files:
        summary["files_processed"] += 1
        summary["json_files"] += 1
        table_name = map_table_name(json_file.stem)

        keys = get_json_keys(json_file)
        if not keys:
            logger.warning(f"No columns found in {json_file.name}. Skipping.")
            continue

       
        log_file_details(json_file, table_name, len(keys))

        if keys:
            mapped_keys = map_columns(keys)
            summary["total_columns"] += len(keys)
            summary["mapped_columns"] += len(mapped_keys)
            summary["unmapped_columns"] += max(len(keys) - len(mapped_keys), 0)
            log_column_mapping(keys, mapped_keys)

            existing_columns = []

            if registry_path.exists():
                with open(registry_path, "r", encoding="utf-8") as f:
                    registry = json.load(f)

                existing_columns = registry.get(table_name, [])

            result = detect_schema_changes(existing_columns, mapped_keys)
            cdc_status["tables"][table_name] = result
            log_schema_status(result)
            summary[result["status"].lower()] += 1
        update_schema_registry(table_name, mapped_keys, registry_path)
        logger.info("Schema Registry Updated Successfully.")
    cdc_path = (
        project_root
        / "metadata"
        / db_type
        / "cdc_status.json"
    )

    with open(cdc_path, "w", encoding="utf-8") as f:
        json.dump(cdc_status, f, indent=4)

    logger.info(f"CDC metadata written to {cdc_path}")
    log_mapping_summary(summary)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        raise
