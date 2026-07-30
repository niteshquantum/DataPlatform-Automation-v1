from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import (
    load_database_config,
    get_project_root
)


def print_header():

    print()
    print("=" * 60)
    print("MSSQL MEDIA EXTRACTION")
    print("=" * 60)


def remove_old_media(media_path: Path):

    if media_path.exists():

        print(f"[INFO] Removing {media_path}")

        shutil.rmtree(media_path)


def media_already_extracted(media_path: Path):

    iso_file = next(
        media_path.rglob("*.iso"),
        None
    )

    return iso_file is not None


def extract_media():

    config = load_database_config("mssql_media")

    project_root = get_project_root()

    archive_file = (
        project_root /
        config["MSSQL_DOWNLOAD_DIRECTORY"] /
        config["MSSQL_MEDIA_NAME"]
    )

    if not archive_file.exists():

        raise FileNotFoundError(
            f"MSSQL media archive not found:\n{archive_file}"
        )

    media_path = (
        project_root /
        config["MSSQL_MEDIA_DIRECTORY"]
    )

    if (
        media_already_extracted(media_path)
        and
        config["FORCE_EXTRACT"].lower() != "true"
    ):

        print()
        print("[INFO] MSSQL media already extracted.")
        print("[INFO] Skipping extraction.")

        return

    if (
        media_path.exists()
        and
        config["FORCE_EXTRACT"].lower() == "true"
    ):

        remove_old_media(media_path)

    media_path.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("Extracting MSSQL installation media...")
    print()

    print("[INFO] Archive :")
    print(archive_file)

    print()

    print("[INFO] Extract Location :")
    print(media_path)

    print()

    with zipfile.ZipFile(
        archive_file,
        "r"
    ) as zip_ref:

        zip_ref.extractall(media_path)

    print("[SUCCESS] MSSQL media extracted successfully.")

    if config["DELETE_ARCHIVE"].lower() == "true":

        archive_file.unlink()

        print("[INFO] Archive deleted.")


def verify_media():

    config = load_database_config("mssql_media")

    media_path = (
        get_project_root() /
        config["MSSQL_MEDIA_DIRECTORY"]
    )

    iso_file = next(
        media_path.rglob("*.iso"),
        None
    )

    if media_path.exists():

        print()
        print("Media Contents:")

        for item in media_path.rglob("*"):

            if item.is_file():

                print(item.relative_to(media_path))

    print()
    print("=" * 60)
    print("MSSQL MEDIA VERIFICATION")
    print("=" * 60)

    if iso_file is None:

        raise Exception(
            "SQL Server ISO not found."
        )

    print("[OK] ISO Found")
    print(iso_file.resolve())
    print("[SUCCESS] MSSQL installation media verified.")

def main():

    print_header()

    extract_media()

    verify_media()


if __name__ == "__main__":

    main()