#!/usr/bin/env python3

"""
Checksum Generator

Generates SHA-256 checksums for all CSV and JSON files
present in the incoming/<database>/ directory.
"""

import sys
import hashlib
from pathlib import Path


def generate_checksum(file_path):
    """
    Generate SHA-256 checksum for a file.

    Args:
        file_path (Path): File path

    Returns:
        str: SHA-256 checksum
    """
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while True:
            chunk = file.read(8192)

            if not chunk:
                break

            sha256.update(chunk)

    return sha256.hexdigest()


def generate_checksums(database):
    """
    Generate checksums for all supported files.

    Args:
        database (str): Database name

    Returns:
        dict
    """

    project_root = Path(__file__).resolve().parent.parent.parent

    incoming_dir = project_root / "incoming" / database

    if not incoming_dir.exists():
        raise FileNotFoundError(
            f"Incoming directory not found: {incoming_dir}"
        )

    checksums = {}

    for file_path in sorted(incoming_dir.iterdir()):

        if file_path.suffix.lower() not in [".csv", ".json"]:
            continue

        checksums[file_path.name] = {
            "checksum": generate_checksum(file_path)
        }

    return checksums


def main():

    if len(sys.argv) < 2:
        print("Usage: python checksum_generator.py <database>")
        sys.exit(1)

    database = sys.argv[1].lower()

    checksums = generate_checksums(database)

    for file_name, details in checksums.items():
        print(f"{file_name} : {details['checksum']}")


if __name__ == "__main__":
    main()