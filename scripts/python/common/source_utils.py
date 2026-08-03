from pathlib import Path


def get_output_filename(source_type: str,
                        source_path: str,
                        config: dict) -> str:
    """
    Returns the filename that should be stored in
    incoming/archive.

    Rules
    -----
    Local      -> Original filename
    GoogleDrive-> Existing DATASET_NAME
    Future:
        Azure Blob -> Blob filename
        S3         -> Object filename
        FTP        -> Remote filename
    """

    source_type = source_type.lower()

    if source_type == "local":
        return Path(source_path).name

    if source_type == "google_drive":
        return config["DATASET_NAME"]

    return config["DATASET_NAME"]




def is_archive_file(file_path: str) -> bool:
    """
    Returns True if dataset is a ZIP archive.
    """

    return Path(file_path).suffix.lower() == ".zip"