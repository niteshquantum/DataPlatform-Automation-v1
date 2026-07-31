from pathlib import Path
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import (
    load_common_config,
    get_project_root
)
from scripts.python.common.dataset_state import (
    build_extraction_state,
    mark_extraction_invalid,
    load_state,
    save_state
)

from scripts.python.common.archive_utils import (
    validate_archive,
    extract_archive,
    list_archive_folders
)


def print_header():
    print()
    print("=" * 60)
    print("DATASET EXTRACTION & MERGE")
    print("=" * 60)




def _folder_has_supported_files(folder_path: Path) -> bool:
    return any(
        p.is_file() and p.suffix.lower() in (".csv", ".json")
        for p in folder_path.iterdir()
    )


def extract_and_merge_zip(archive_file: Path, incoming_path: Path):
    print()
    print("Extracting and merging dataset...")
    print()

    try:
        with zipfile.ZipFile(archive_file, "r") as zip_ref:
            for member in zip_ref.infolist():
                target_path = incoming_path / member.filename

                if member.is_dir():
                    target_path.mkdir(parents=True, exist_ok=True)
                    continue

                target_path.parent.mkdir(parents=True, exist_ok=True)

                if target_path.exists():
                    try:
                        target_path.unlink()
                    except PermissionError:
                        print(f"[WARNING] Cannot delete {target_path}. Trying overwrite...")

                try:
                    with zip_ref.open(member) as source, open(target_path, "wb") as target:
                        shutil.copyfileobj(source, target)
                except PermissionError as e:
                    print(f"[ERROR] Permission Denied for file: {target_path}")
                    raise e

    except NotImplementedError:
        print("[INFO] Unsupported ZIP compression detected.")
        print("[INFO] Falling back to 7-Zip extraction...")
        extract_archive(archive_file, incoming_path)

    print("[SUCCESS] Dataset extracted and merged successfully.")


def extract_dataset():
    config = load_common_config("dataset")
    project_root = get_project_root()

    archive_file = (
        project_root /
        config["DOWNLOAD_DIRECTORY"] /
        config["DATASET_NAME"]
    )

    validate_archive(archive_file)

    incoming_path = project_root / "incoming"
    incoming_path.mkdir(parents=True, exist_ok=True)

    expected_folders = list_archive_folders(archive_file)

    state = load_state()

    force = config.get("FORCE_EXTRACT", "false").lower() == "true"

    if not force and state.get("extraction_status") == "EXTRACTED_COMPLETE":
        current_state_archive = state.get("archive_path")
        current_state_identity = state.get("dataset_identity")
        actual_identity = None
        try:
            from scripts.python.common.dataset_state import _sha256
            actual_identity = _sha256(archive_file)
        except Exception:
            actual_identity = None

        state_archive_matches = (
            current_state_archive is not None
            and Path(current_state_archive).exists()
            and Path(current_state_archive).resolve() == archive_file.resolve()
        )

        if state_archive_matches and actual_identity == current_state_identity:
            missing = [
                f for f in expected_folders
                if not (incoming_path / f).exists()
                or not _folder_has_supported_files(incoming_path / f)
            ]
            if not missing:
                print()
                print("[INFO] Archive already extracted successfully.")
                print("[INFO] Skipping extraction.")
                return
            else:
                print()
                print(f"[WARNING] Missing or empty extracted folders: {missing}")
                print("[INFO] Re-extracting...")
        else:
            print()
            print("[WARNING] State does not match current archive.")
            print("[INFO] Re-extracting...")

    extract_and_merge_zip(archive_file, incoming_path)

    actual_folders = sorted(
        str(p.relative_to(incoming_path))
        for p in incoming_path.iterdir()
        if p.is_dir()
    )

    missing = [f for f in expected_folders if f not in actual_folders]
    if missing:
        mark_extraction_invalid(f"Missing folders after extraction: {missing}")
        raise RuntimeError(f"Extraction incomplete. Missing: {missing}")

    state = build_extraction_state(config, archive_file, incoming_path)
    save_state(state)

    if config.get("DELETE_ARCHIVE", "false").lower() == "true":
        archive_file.unlink()
        print("[INFO] Archive deleted after successful extraction.")


def verify_dataset():
    config = load_common_config("dataset")
    project_root = get_project_root()
    incoming = project_root / "incoming"

    archive_file = (
        project_root /
        config["DOWNLOAD_DIRECTORY"] /
        config["DATASET_NAME"]
    )

    print()
    print("=" * 60)
    print("DATASET VERIFICATION")
    print("=" * 60)

    if not archive_file.exists():
        if incoming.exists() and any(incoming.iterdir()):
            print("[OK] Incoming folder has data (Archive already deleted).")
            return
        else:
            raise Exception("Incoming folder is empty.")

    zip_top_folders = list_archive_folders(archive_file)

    for folder in zip_top_folders:
        folder_path = incoming / folder
        if folder_path.exists():
            print(f"[OK] Verified folder: {folder}")
        else:
            raise Exception(f"Verification failed: {folder} folder not found.")


def main():
    print_header()
    extract_dataset()
    verify_dataset()


if __name__ == "__main__":
    main()
