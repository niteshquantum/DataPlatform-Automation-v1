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
    save_state,
    load_state,
    _sha256
)

from scripts.python.common.archive_utils import (
    validate_archive,
    list_archive_folders
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


def _resolve_database(config, source_type, source_path):
    database = (
        os.getenv("DATABASE")
        or config.get("DATABASE")
    )
    if database:
        return database.strip().lower()

    if source_type and source_type.lower() == "local" and source_path:
        source = Path(source_path)
        if source.exists() and source.is_dir():
            return source.name.strip().lower()

    return None


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

    database = _resolve_database(config, source_type, source_path)

    if not source_type:
        if config.get("DATASET_URL"):
            source_type = "google_drive"
        else:
            raise ValueError("SOURCE_TYPE is not configured.")

    downloader = get_downloader(source_type)

    output_filename = get_output_filename(
        source_type=source_type,
        source_path=source_path,
        config=config
    )

    archive = is_archive_file(output_filename)

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

    source = Path(source_path) if source_path else None

    if source and source.is_dir():

        output_file = destination_directory

    else:

        output_file = (
            destination_directory /
            output_filename
        )

    force = (
        os.getenv("FORCE_DOWNLOAD")
        or config.get("FORCE_DOWNLOAD", "false")
    ).lower() == "true"

    if output_file.exists() and not force:

        if archive:

            print()
            print("[INFO] Checking existing archive...")

            try:
                validate_archive(output_file)
            except Exception as exc:
                print()
                print(f"[WARNING] Archive validation failed : {exc}")
                print("[INFO] Downloading current source.")
            else:
                print("[INFO] Existing archive is valid.")
                print("[INFO] Checking source identity...")

                state = load_state()
                prev_source_type = state.get("source_type")
                prev_source_url = state.get("source_url")
                prev_archive_sha256 = state.get("archive_sha256")

                if source_type.lower() == "google_drive":
                    current_source_url = (
                        os.getenv("SOURCE_PATH")
                        or config.get("SOURCE_PATH")
                        or config.get("DATASET_URL", "")
                    )
                else:
                    current_source_url = (
                        os.getenv("SOURCE_PATH")
                        or config.get("SOURCE_PATH")
                        or ""
                    )

                current_archive_sha256 = _sha256(output_file)

                has_required_fields = (
                    prev_source_type is not None
                    and prev_source_url is not None
                    and prev_archive_sha256 is not None
                )

                if has_required_fields \
                   and prev_source_type == source_type \
                   and prev_source_url == current_source_url \
                   and prev_archive_sha256 == current_archive_sha256:
                    print("[INFO] Source identity matches.")
                    print("[INFO] Reusing existing archive.")
                    print("[INFO] Download skipped.")
                    print()
                    print("=" * 60)
                    print("DATASET SUMMARY")
                    print("=" * 60)
                    print(f"Source Type : {source_type.upper()}")

                    print(f"Destination : {destination_directory}")
                    print("Input Type  : ZIP Archive")

                    try:
                        detected_databases = list_archive_folders(output_file)
                    except Exception:
                        detected_databases = []

                    if detected_databases:
                        print("Detected Databases:")
                        for db in detected_databases:
                            print(f"  {db}")

                    print("Status      : SKIPPED")
                    print()
                    return output_file
                else:
                    if not has_required_fields:
                        print("[INFO] No previous dataset state found.")
                    else:
                        print("[WARNING] Source identity mismatch.")
                        print(f"[WARNING] Current source: {source_type} / {current_source_url}")
                        print(f"[WARNING] Previous source: {prev_source_type} / {prev_source_url}")
                    print("[INFO] Downloading current source.")

        elif source and source.is_file():

            print()
            print("[INFO] Dataset already exists:")
            print(f"Location : {output_file}")

            print()
            print("=" * 60)
            print("DATASET SUMMARY")
            print("=" * 60)
            print(f"Source Type : {source_type.upper()}")

            if database:
                print(f"Database    : {database.lower()}")

            print(f"Destination : {destination_directory}")

            if source_path:
                print(f"Source Path : {source_path}")

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

    if source_path:
        if source_type and source_type.lower() == "google_drive":
            print(f"Source URL  : {source_path}")
        else:
            print(f"Source Path : {source_path}")
    print(f"Destination : {destination_directory}")

    print()

    if source_type.lower() == "google_drive":

        print("Downloading dataset from Google Drive...")

    elif source_type.lower() == "local":

        if source and source.is_dir():

            print("Copying local dataset folder...")

        elif archive:

            print("Copying local ZIP archive...")

        else:

            print("Copying local dataset file...")

    else:

        print("Acquiring dataset...")

    print()

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

            try:
                detected_databases = list_archive_folders(output_file)
            except Exception:
                detected_databases = []

            if source_type.lower() == "google_drive":
                current_source_url = (
                    os.getenv("SOURCE_PATH")
                    or config.get("SOURCE_PATH")
                    or config.get("DATASET_URL", "")
                )
            else:
                current_source_url = (
                    os.getenv("SOURCE_PATH")
                    or config.get("SOURCE_PATH")
                    or ""
                )

            state = build_download_state(
                config,
                output_file,
                source_type,
                current_source_url,
                detected_databases=detected_databases
            )

            save_state(state)

            print()
            print("[INFO] Archive downloaded successfully.")
            print(f"[INFO] SHA256: {state['archive_sha256']}")
            if detected_databases:
                print("Detected Databases:")
                for db in detected_databases:
                    print(f"  {db}")
            print("[INFO] Dataset state updated.")

            print()
            print("=" * 60)
            print("DATASET SUMMARY")
            print("=" * 60)
            print(f"Source Type : {source_type.upper()}")

            print(f"Destination : {destination_directory}")
            print("Input Type  : ZIP Archive")

            if detected_databases:
                print("Detected Databases:")
                for db in detected_databases:
                    print(f"  {db}")

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

    else:

        downloader.download(
            config,
            str(output_file)
        )

    print()

    print("Copy operation completed successfully.")

    print(f"Destination : {output_file}")

    print()
    print("=" * 60)
    print("DATASET SUMMARY")
    print("=" * 60)

    print(f"Source Type : {source_type.upper()}")

    if database:
        print(f"Database    : {database.lower()}")

    print(f"Destination : {destination_directory}")

    if source_path:
        if source_type and source_type.lower() == "google_drive":
            print(f"Source URL  : {source_path}")
        else:
            print(f"Source Path : {source_path}")

    if source and source.is_dir():

        input_type = "Folder"

    elif source and source.suffix.lower() == ".csv":

        input_type = "CSV File"

    elif source and source.suffix.lower() == ".json":

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