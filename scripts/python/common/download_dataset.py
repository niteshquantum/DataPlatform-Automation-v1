import os
import tempfile
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import (
    load_common_config,
    get_project_root
)

from scripts.python.common.dataset_state import (
    build_download_state,
    save_state
)

from scripts.python.common.archive_utils import (
    validate_archive
)

from scripts.python.common.factory.downloader_factory import (
    get_downloader
)

from scripts.python.common.source_utils import (
    get_output_filename,
    is_archive_file
)


def print_header():

    print()
    print("=" * 60)
    print("DATASET DOWNLOAD")
    print("=" * 60)


def create_directory(directory: Path):

    directory.mkdir(
        parents=True,
        exist_ok=True
    )


def download_dataset():

    config = load_common_config("dataset")

    project_root = get_project_root()

    source_type = (
        os.getenv("SOURCE_TYPE")
        or config.get("SOURCE_TYPE")
    )

    source_path = (
        os.getenv("SOURCE_PATH")
        or config.get("SOURCE_PATH")
    )

    database = (
        os.getenv("DATABASE")
        or config.get("DATABASE")
    )

    if not source_type:
        raise ValueError("SOURCE_TYPE is not configured.")

    downloader = get_downloader(source_type)

    output_filename = get_output_filename(
        source_type=source_type,
        source_path=source_path,
        config=config
    )

    archive = is_archive_file(output_filename)

    # ---------------------------------------
    # Decide destination
    # ---------------------------------------

    if archive:

        destination_directory = (
            project_root /
            config["DOWNLOAD_DIRECTORY"]
        )

    else:

        if not database:
            raise ValueError(
                "DATABASE is required for non-archive datasets."
            )

        destination_directory = (
            project_root /
            "incoming" /
            database.lower()
        )

    create_directory(destination_directory)

    source = Path(source_path)

    if source.is_dir():

        output_file = destination_directory

    else:

        output_file = (
            destination_directory /
            output_filename
        )

    force = (
        config.get(
            "FORCE_DOWNLOAD",
            "false"
        ).lower() == "true"
    )

    if source.is_file():

        if output_file.exists() and not force:

            print()
            print("[INFO] Dataset already exists:")
            print(f"Location : {output_file}")

            if archive:

                try:
                    validate_archive(output_file)

                    print("[INFO] Existing archive already verified.")
                    print("[INFO] Download skipped.")

                    print()
                    print("=" * 60)
                    print("DATASET SUMMARY")
                    print("=" * 60)
                    print(f"Source Type : {source_type.upper()}")

                    if database:
                        print(f"Database    : {database.lower()}")

                    print(f"Destination : {destination_directory}")
                    print("Input Type  : ZIP Archive")
                    print("Status      : SKIPPED")
                    print()

                    return output_file

                except Exception as exc:

                    print()
                    print(f"[WARNING] Archive validation failed : {exc}")
                    print("[INFO] Re-downloading archive...")

            else:

                print("[INFO] Dataset already exists.")
                print(f"Location : {output_file}")

                print()
                print("=" * 60)
                print("DATASET SUMMARY")
                print("=" * 60)
                print(f"Source Type : {source_type.upper()}")

                if database:
                    print(f"Database    : {database.lower()}")

                print(f"Destination : {destination_directory}")
                if source.is_dir():

                    input_type = "Folder"

                elif source.suffix.lower() == ".csv":

                    input_type = "CSV File"

                elif source.suffix.lower() == ".json":

                    input_type = "JSON File"

                else:

                    input_type = "File"

                print(f"Input Type  : {input_type}")
                print("Status      : SKIPPED")
                print()

                return output_file

    print()

    print(f"Source Type : {source_type.upper()}")

    if database:
        print(f"Database    : {database.lower()}")

    print(f"Source      : {source_path}")
    print(f"Destination : {destination_directory}")

    print()

    if source_type.lower() == "google_drive":

        print("Downloading dataset from Google Drive...")

    elif source_type.lower() == "local":

        source = Path(source_path)

        if source.is_dir():

            print("Copying local dataset folder...")

        elif archive:

            print("Copying local ZIP archive...")

        else:

            print("Copying local dataset file...")

    else:

        print("Acquiring dataset...")

    print()

    # ---------------------------------------
    # ZIP download
    # ---------------------------------------

    if archive:

        tmp_path = None

        try:

            with tempfile.NamedTemporaryFile(
                dir=destination_directory,
                delete=False,
                suffix=".tmp"
            ) as tmp:

                tmp_path = Path(tmp.name)

            downloader.download(
                config,
                str(tmp_path)
            )

            validate_archive(tmp_path)

            tmp_path.replace(output_file)

            state = build_download_state(
                config,
                output_file
            )

            save_state(state)

            print()

            print("Download completed successfully.")

            print(f"Archive : {output_file}")

            print()

            print("=" * 60)
            print("DATASET SUMMARY")
            print("=" * 60)

            print(f"Source Type : {source_type.upper()}")

            if database:
                print(f"Database    : {database.lower()}")

            print(f"Destination : {destination_directory}")

            print(f"Input Type  : {input_type}")

            if source.is_dir():

                print(f"Files Found : {copied}")

            print("Status      : SUCCESS")

            print()

            return output_file

        except Exception:

            if tmp_path and tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

            if output_file.exists():

                try:
                    validate_archive(output_file)

                except Exception:
                    output_file.unlink(missing_ok=True)

            raise

    # ---------------------------------------
    # CSV / JSON / Folder
    # ---------------------------------------

    downloader.download(
        config,
        str(output_file)
    )
    

    print()

    print("Copy operation completed successfully.")

    print(f"Location : {output_file}")

    print()
    print("=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)

    print(f"Source Type : {source_type.upper()}")

    if database:
        print(f"Database    : {database.lower()}")

    print(f"Destination : {destination_directory}")

    if archive:

        input_type = "ZIP Archive"

    elif source.is_dir():

        input_type = "Folder"

    elif source.suffix.lower() == ".csv":

        input_type = "CSV File"

    elif source.suffix.lower() == ".json":

        input_type = "JSON File"

    else:

        input_type = "File"

    print(f"Input Type  : {input_type}")

    print("Status      : SUCCESS")

    print()

    return output_file


def main():

    print_header()

    download_dataset()


if __name__ == "__main__":
    main()