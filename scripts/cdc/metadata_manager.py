#!/usr/bin/env python3

"""
Metadata Manager

Handles reading and writing CDC migration metadata.
"""

import json
from pathlib import Path


# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Metadata Directory
METADATA_DIR = PROJECT_ROOT / "metadata" / "cdc"

# Metadata File
METADATA_FILE = METADATA_DIR / "migration_state.json"


def load_metadata():
    """
    Load existing migration metadata.

    Returns:
        dict
    """

    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    if not METADATA_FILE.exists():
        return {}

    try:

        with open(
            METADATA_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception:

        return {}


def save_metadata(metadata):
    """
    Save migration metadata.

    Args:
        metadata (dict)
    """

    METADATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            metadata,
            file,
            indent=4
        )


def get_file_metadata(file_name):
    """
    Return metadata for a specific file.

    Args:
        file_name (str)

    Returns:
        dict
    """

    metadata = load_metadata()

    return metadata.get(file_name, {})


def update_file_metadata(file_name, file_metadata):
    """
    Update metadata for a specific file.

    Args:
        file_name (str)
        file_metadata (dict)
    """

    metadata = load_metadata()

    metadata[file_name] = file_metadata

    save_metadata(metadata)