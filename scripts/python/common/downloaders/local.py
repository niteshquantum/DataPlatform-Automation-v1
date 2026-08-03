import os
import shutil
from pathlib import Path

SOURCE_TYPE = "local"


def download(config, output_path):
    """
    Copy a dataset from the local file system.
    Supports:
      - Single CSV/JSON/ZIP file
      - Folder containing multiple CSV/JSON files
    """

    source_path = os.getenv("SOURCE_PATH")

    if source_path:
        source_path = source_path.strip()

    if not source_path:
        source_path = config.get("SOURCE_PATH")

    if not source_path:
        raise ValueError(
            "SOURCE_PATH is not configured."
        )

    source = Path(source_path)

    if not source.exists():
        raise FileNotFoundError(
            f"Local dataset not found: {source}"
        )

    destination = Path(output_path)

    # --------------------------
    # Single File
    # --------------------------
    if source.is_file():

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        shutil.copy2(
            source,
            destination
        )

        return

    # --------------------------
    # Folder
    # --------------------------
    if source.is_dir():

        destination.mkdir(
            parents=True,
            exist_ok=True
        )

        copied = 0

        for file in source.iterdir():

            if (
                file.is_file()
                and file.suffix.lower() in (
                    ".csv",
                    ".json"
                )
            ):

                shutil.copy2(
                    file,
                    destination / file.name
                )

                copied += 1

        if copied == 0:
            raise ValueError(
                f"No CSV/JSON files found in: {source}"
            )

        return

    raise ValueError(
        f"Unsupported source: {source}"
    )