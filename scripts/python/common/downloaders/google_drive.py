import os
from pathlib import Path

import gdown

SOURCE_TYPE = "google_drive"


def download(config, output_path):
    source_path = os.getenv("SOURCE_PATH")

    if source_path:
        source_path = source_path.strip()

    if not source_path:
        source_path = config.get("SOURCE_PATH")

    if not source_path:
        source_path = config.get("DATASET_URL")

    if not source_path:
        raise ValueError(
            "SOURCE_PATH or DATASET_URL is not configured."
        )

    destination = Path(output_path)

    print()
    print("Google Drive Download")
    print("---------------------")
    print(f"Source URL  : {source_path}")
    print(f"Output File : {destination.name}")
    print(f"Destination : {destination.parent}")
    print()

    gdown.download(
        source_path,
        output_path,
        quiet=False
    )

    if not destination.exists():
        raise RuntimeError(
            "Google Drive download failed."
        )

    size_mb = destination.stat().st_size / (1024 * 1024)

    print()
    print("Download Summary")
    print("----------------")
    print(f"File Name : {destination.name}")
    print(f"Size      : {size_mb:.2f} MB")