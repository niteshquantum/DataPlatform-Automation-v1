from pathlib import Path
import sys

import gdown

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import (
    load_database_config,
    get_project_root
)


def print_header():

    print()
    print("=" * 60)
    print("MSSQL MEDIA DOWNLOAD")
    print("=" * 60)


def create_directory(directory: Path):

    directory.mkdir(parents=True, exist_ok=True)


def download_media():

    config = load_database_config("mssql_media")

    project_root = get_project_root()

    download_directory = (
        project_root /
        config["MSSQL_DOWNLOAD_DIRECTORY"]
    )

    create_directory(download_directory)

    output_file = (
        download_directory /
        config["MSSQL_MEDIA_NAME"]
    )

    if (
        output_file.exists()
        and
        config["FORCE_DOWNLOAD"].lower() != "true"
    ):
        print()
        print("[INFO] MSSQL installation media already exists:")
        print(output_file)
        return output_file

    print()
    print("Downloading MSSQL installation media...")
    print()

    gdown.download(
        config["MSSQL_MEDIA_URL"],
        str(output_file),
        quiet=False
    )

    print()
    print("[SUCCESS] MSSQL media downloaded successfully.")
    print(output_file)

    return output_file


def main():

    print_header()

    download_media()


if __name__ == "__main__":
    main()