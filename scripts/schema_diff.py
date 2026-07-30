#!/usr/bin/env python
"""
Schema Diff Script

Compares metadata/schema_registry.json with snapshot files in metadata/current_schema/
and generates metadata/schema_changes.json with detected differences.
"""

import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_schema_registry(registry_path):
    """
    Load schema_registry.json.
    
    Args:
        registry_path: Path to schema_registry.json
        
    Returns:
        Dictionary with table schemas
    """
    try:
        if registry_path.exists():
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry = json.load(f)
                logger.info(f"Loaded schema registry: {len(registry)} table(s)")
                return registry
        else:
            logger.warning(f"Schema registry not found: {registry_path}")
            return {}
    except Exception as e:
        logger.error(f"Error loading schema registry: {e}")
        return {}


def load_snapshot(snapshot_path):
    """
    Load snapshot file for a table.
    
    Args:
        snapshot_path: Path to snapshot JSON file
        
    Returns:
        List of columns or None if snapshot doesn't exist
    """
    try:
        if snapshot_path.exists():
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                columns = data.get("columns", [])
                logger.info(f"Loaded snapshot {snapshot_path.name}: {len(columns)} column(s)")
                return columns
        else:
            logger.info(f"Snapshot not found: {snapshot_path.name}")
            return None
    except Exception as e:
        logger.error(f"Error loading snapshot {snapshot_path}: {e}")
        return None


def save_snapshot(snapshot_path, columns):
    """
    Save snapshot file for a table.
    
    Args:
        snapshot_path: Path to snapshot JSON file
        columns: List of column names
    """
    try:
        snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        snapshot_data = {"columns": columns}
        with open(snapshot_path, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, indent=2)
            logger.info(f"Saved snapshot {snapshot_path.name}: {len(columns)} column(s)")
    except Exception as e:
        logger.error(f"Error saving snapshot {snapshot_path}: {e}")


def compare_schemas(current_columns, snapshot_columns):
    """
    Compare current schema with snapshot to detect changes.
    
    Args:
        current_columns: List of columns from schema_registry.json
        snapshot_columns: List of columns from snapshot file (or None)
        
    Returns:
        Dictionary with new_columns, removed_columns, existing_columns
    """
    if snapshot_columns is None:
        # If no snapshot exists, treat all columns as new
        return {
            "new_columns": current_columns,
            "removed_columns": [],
            "existing_columns": []
        }
    
    current_set = set(current_columns)
    snapshot_set = set(snapshot_columns)
    
    new_columns = list(current_set - snapshot_set)
    removed_columns = list(snapshot_set - current_set)
    existing_columns = list(current_set & snapshot_set)
    
    # Preserve order from current schema
    new_columns_ordered = [col for col in current_columns if col in new_columns]
    existing_columns_ordered = [col for col in current_columns if col in existing_columns]
    
    return {
        "new_columns": new_columns_ordered,
        "removed_columns": removed_columns,
        "existing_columns": existing_columns_ordered
    }


def main():
    """
    Main function to compare schemas and generate diff report.
    """
    logger.info("Starting schema diff analysis...")
    
    # Define paths
    project_root = Path(__file__).parent.parent
    registry_path = project_root / "metadata" / "schema_registry.json"
    snapshot_dir = project_root / "metadata" / "current_schema"
    changes_path = project_root / "metadata" / "schema_changes.json"
    
    # Create snapshot directory if needed
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Using snapshot directory: {snapshot_dir}")
    
    # Load schema registry
    schema_registry = load_schema_registry(registry_path)
    
    if not schema_registry:
        logger.warning("No tables found in schema registry")
        return
    
    # Compare each table and generate changes report
    changes_report = {}
    
    for table_name, columns in schema_registry.items():
        logger.info(f"Analyzing table: {table_name}")
        
        # Load existing snapshot
        snapshot_path = snapshot_dir / f"{table_name}.json"
        snapshot_columns = load_snapshot(snapshot_path)
        
        # Compare schemas
        comparison = compare_schemas(columns, snapshot_columns)
        changes_report[table_name] = comparison
        
        # Log changes
        if comparison["new_columns"]:
            logger.info(f"  New columns: {comparison['new_columns']}")
        if comparison["removed_columns"]:
            logger.warning(f"  Removed columns: {comparison['removed_columns']}")
        if comparison["existing_columns"]:
            logger.info(f"  Existing columns: {len(comparison['existing_columns'])}")
        
        # Update snapshot file
        save_snapshot(snapshot_path, columns)
    
    # Save changes report
    try:
        with open(changes_path, 'w', encoding='utf-8') as f:
            json.dump(changes_report, f, indent=2)
            logger.info(f"Generated schema changes report: {changes_path}")
    except Exception as e:
        logger.error(f"Error saving schema changes report: {e}")
    
    logger.info("Schema diff analysis completed successfully")


if __name__ == "__main__":
    main()