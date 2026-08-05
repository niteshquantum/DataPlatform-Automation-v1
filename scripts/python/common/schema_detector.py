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
from decimal import Decimal
from functools import lru_cache

from column_mapper import map_columns
from datatype_detector import detect_datatype
from datatype_override import resolve_datatype

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
DEFAULT_SAMPLING_SIZE = 100
DEFAULT_DATATYPE = "VARCHAR"


@lru_cache(maxsize=1)
def _load_datatype_rules():
    """Load datatype rules once, falling back to the existing defaults."""
    config_path = (
        Path(__file__).parent.parent.parent.parent
        / "config"
        / "datatype_rules.json"
    )

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        logger.error(f"Error reading datatype rules {config_path}: {e}")
        return DEFAULT_SAMPLING_SIZE, DEFAULT_DATATYPE

    if not isinstance(rules, dict):
        logger.error(f"Invalid datatype rules configuration: {config_path}")
        return DEFAULT_SAMPLING_SIZE, DEFAULT_DATATYPE

    sampling_size = rules.get("sampling_size")
    default_type = rules.get("default_type")

    if (
        not isinstance(sampling_size, int)
        or isinstance(sampling_size, bool)
        or sampling_size <= 0
        or not isinstance(default_type, str)
        or not default_type.strip()
    ):
        logger.error(f"Invalid datatype rules configuration: {config_path}")
        return DEFAULT_SAMPLING_SIZE, DEFAULT_DATATYPE

    return sampling_size, default_type


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


def get_csv_column_samples(file_path, headers):
    """Collect up to the configured number of values for every CSV column."""
    samples = {header: [] for header in headers}
    sampling_size, _ = _load_datatype_rules()

    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            next(reader, None)

            for record_number, row in enumerate(reader):
                if record_number >= sampling_size:
                    break
                for index, header in enumerate(headers):
                    if index < len(row):
                        samples[header].append(row[index])
    except Exception as e:
        logger.error(f"Error sampling CSV file {file_path}: {e}")

    return samples


def get_json_column_samples(file_path, keys):
    """Collect up to the configured number of values for every JSON key."""
    samples = {key: [] for key in keys}
    sampling_size, _ = _load_datatype_rules()

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f, parse_float=Decimal)

        records = data if isinstance(data, list) else [data]
        for record in records[:sampling_size]:
            if not isinstance(record, dict):
                continue
            for key in keys:
                samples[key].append(record.get(key))
    except Exception as e:
        logger.error(f"Error sampling JSON file {file_path}: {e}")

    return samples


def get_mapped_column_samples(columns, mapped_columns, samples):
    """Combine source samples that resolve to the same mapped column name."""
    mapped_samples = {}

    for column, mapped_column in zip(columns, mapped_columns):
        mapped_samples.setdefault(mapped_column, []).extend(samples.get(column, []))

    return mapped_samples


def update_datatype_metadata(table_name, datatypes, metadata_path):
    """Create or update the datatype metadata without affecting schema registry."""
    try:
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        if metadata_path.exists():
            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        existing_datatypes = metadata.get(table_name, {})
        if not isinstance(existing_datatypes, dict):
            existing_datatypes = {}
        existing_datatypes = {
            column: (
                datatype
                if isinstance(datatype, dict)
                else {"detected_type": datatype}
            )
            for column, datatype in existing_datatypes.items()
        }
        existing_datatypes.update(datatypes)
        metadata[table_name] = existing_datatypes

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f"Error updating datatype metadata: {e}")


def detect_and_update_datatypes(table_name, columns, mapped_columns, samples, metadata_path):
    """Detect mapped-column datatypes and save them to datatype metadata."""
    mapped_samples = get_mapped_column_samples(columns, mapped_columns, samples)
    _, default_type = _load_datatype_rules()
    detected_datatypes = {
        column: (
            detected_type
            if (detected_type := detect_datatype(column, values)) != DEFAULT_DATATYPE
            else default_type
        )
        for column, values in mapped_samples.items()
    }
    datatypes = {
        column: {
            "detected_type": detected_type,
            "final_type": resolve_datatype(table_name, column, detected_type),
        }
        for column, detected_type in detected_datatypes.items()
    }

    for column, datatype in detected_datatypes.items():
        logger.info(f"Column {column} detected datatype: {datatype}")

    update_datatype_metadata(table_name, datatypes, metadata_path)


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
    datatype_metadata_path = (
        project_root.parent
        / "metadata"
        / "datatype_metadata.json"
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
            mapped_columns = map_columns(headers)
            samples = get_csv_column_samples(csv_file, headers)
            detect_and_update_datatypes(
                table_name, headers, mapped_columns, samples, datatype_metadata_path
            )
            update_schema_registry(table_name, mapped_columns, registry_path)
    
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
            mapped_columns = map_columns(keys)
            samples = get_json_column_samples(json_file, keys)
            detect_and_update_datatypes(
                table_name, keys, mapped_columns, samples, datatype_metadata_path
            )
            update_schema_registry(table_name, mapped_columns, registry_path)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        import traceback
        traceback.print_exc()
        raise
