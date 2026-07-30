#!/usr/bin/env python3

"""
Change Detector

Compares current file checksums with previously stored metadata.
"""

from metadata_manager import (
    get_file_metadata,
    update_file_metadata
)


def detect_changes(current_checksums):
    """
    Detect changes between current and previous checksums.
    """

    results = {}

    # Current files
    current_files = set(current_checksums.keys())

    # Previous files (stored in metadata)
    try:
        from metadata_manager import load_metadata
        previous_metadata = load_metadata()
    except Exception:
        previous_metadata = {}

    previous_files = set(previous_metadata.keys())

    # --------------------------------------------------
    # NEW / CHANGED / UNCHANGED
    # --------------------------------------------------
    for file_name, details in current_checksums.items():

        current_checksum = details["checksum"]

        previous_file_metadata = get_file_metadata(file_name)
        previous_checksum = previous_file_metadata.get("checksum")

        if previous_checksum is None:
            status = "NEW"

        elif previous_checksum == current_checksum:
            status = "UNCHANGED"

        else:
            status = "CHANGED"

        results[file_name] = {
            "status": status,
            "checksum": current_checksum
        }

        update_file_metadata(
            file_name,
            {
                "checksum": current_checksum
            }
        )

    # --------------------------------------------------
    # DELETED FILES
    # --------------------------------------------------
    deleted_files = previous_files - current_files

    for file_name in deleted_files:
        results[file_name] = {
            "status": "DELETED"
        }

    return results