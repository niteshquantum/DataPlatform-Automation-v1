#!/usr/bin/env python
"""
Schema Version Manager

Reads metadata/schema_registry.json and metadata/schema_versions.json, then updates
version history for table schemas whenever new columns are detected.
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


def load_json(path):
    try:
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading JSON from {path}: {e}")
        return {}


def save_json(path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved JSON to {path}")
    except Exception as e:
        logger.error(f"Error saving JSON to {path}: {e}")


def get_current_table_version(table_info):
    if not table_info:
        return 0
    return table_info.get('current_version', 0)


def build_version_entry(version, columns):
    return {
        'version': version,
        'timestamp': datetime.now().isoformat(),
        'columns': columns
    }


def update_table_version(table_name, current_columns, versions_data):
    tables = versions_data.setdefault('tables', {})
    table_info = tables.get(table_name, {})
    history = table_info.setdefault('history', [])
    current_version = get_current_table_version(table_info)

    if not history:
        new_version = 1
        history.append(build_version_entry(new_version, current_columns))
        table_info['current_version'] = new_version
        logger.info(f"Initialized version tracking for {table_name} at version {new_version}")
        return True

    last_columns = history[-1].get('columns', [])
    if current_columns != last_columns:
        new_version = current_version + 1
        history.append(build_version_entry(new_version, current_columns))
        table_info['current_version'] = new_version
        logger.info(f"Updated {table_name} to version {new_version}")
        return True

    logger.info(f"No schema change detected for {table_name}")
    return False


def main():
    logger.info('Starting schema version manager...')

    project_root = Path(__file__).parent.parent
    registry_path = project_root / 'metadata' / 'schema_registry.json'
    versions_path = project_root / 'metadata' / 'schema_versions.json'

    schema_registry = load_json(registry_path)
    schema_versions = load_json(versions_path)

    if not schema_registry:
        logger.warning('No schema registry data found.')
        return

    changes_made = False
    for table_name, columns in schema_registry.items():
        logger.info(f"Processing table {table_name}")
        changed = update_table_version(table_name, columns, schema_versions)
        changes_made = changes_made or changed

    if changes_made:
        save_json(versions_path, schema_versions)
        logger.info('Schema versions updated successfully.')
    else:
        logger.info('No version updates were necessary.')


if __name__ == '__main__':
    main()