from pathlib import Path


def get_output_filename(source_type, source_path, config):

    if source_type is None:
        return config["DATASET_NAME"]

    source_type = source_type.lower()

    if source_type == "local":
        return Path(source_path).name

    if source_type == "google_drive":
        return config["DATASET_NAME"]

    return config["DATASET_NAME"]


def is_archive_file(file_path):
    return Path(file_path).suffix.lower() == ".zip"