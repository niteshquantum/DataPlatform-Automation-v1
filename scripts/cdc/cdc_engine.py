#!/usr/bin/env python3

import sys
import json

from checksum_generator import generate_checksums
from change_detector import detect_changes


def run(database):

    current_checksums = generate_checksums(database)

    results = detect_changes(current_checksums)

    changed_files = []
    skipped_files = []

    for file_name, details in results.items():

        if details["status"] in ["NEW", "CHANGED", "DELETED"]:
            changed_files.append(file_name)
        else:
            skipped_files.append(file_name)

    output = {
        "changed_files": changed_files,
        "skipped_files": skipped_files,
        "results": results
    }

    return output


def main():

    if len(sys.argv) < 2:
        print("Usage: python cdc_engine.py <database>")
        sys.exit(1)

    result = run(sys.argv[1].lower())

    print(json.dumps(result, indent=4))

    if result["changed_files"]:
        sys.exit(0)

    sys.exit(100)


if __name__ == "__main__":
    main()