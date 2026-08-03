import os
import gdown

SOURCE_TYPE = "google_drive"

def download(config, output_path):
    """
    Download a dataset from Google Drive.
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

    dataset_url = (
        os.getenv("DATASET_URL")
        or config.get("DATASET_URL")
    )

    gdown.download(
        dataset_url,
        output_path,
        quiet=False
    )