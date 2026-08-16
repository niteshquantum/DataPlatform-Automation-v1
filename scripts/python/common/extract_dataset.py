from pathlib import Path
import shutil
import sys
import zipfile
import os

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import (
    load_common_config,
    get_project_root
)

from scripts.python.common.source_utils import (
    get_output_filename,
    is_archive_file
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
    print("DATASET PREPARATION")
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

    source_type = (
        os.getenv("SOURCE_TYPE")
        or config.get("SOURCE_TYPE")
    )

    source_path = (
        os.getenv("SOURCE_PATH")
        or config.get("SOURCE_PATH")
    )

    output_filename = get_output_filename(
        source_type=source_type,
        source_path=source_path,
        config=config
    )
    project_root = get_project_root()

    archive_file = (
        project_root /
        config["DOWNLOAD_DIRECTORY"] /
        output_filename
    )

    if not is_archive_file(output_filename):

        print()
        print("[INFO] No extraction required.")


        return

    validate_archive(archive_file)

    incoming_path = project_root / "incoming"
    incoming_path.mkdir(parents=True, exist_ok=True)

    expected_folders = list_archive_folders(archive_file)

    state = load_state()

    force = config.get("FORCE_EXTRACT", "false").lower() == "true"

    download_ts = state.get("download_timestamp")
    extraction_ts = state.get("extraction_timestamp")
    fresh_download = bool(
        download_ts
        and (not extraction_ts or download_ts > extraction_ts)
    )

    can_skip = (
        not force
        and not fresh_download
        and state.get("extraction_status") == "EXTRACTED_COMPLETE"
    )

    if fresh_download:
        print()
        print("[INFO] Fresh archive download detected:")
        print(f"[INFO] Last Download   : {download_ts}")
        print("[INFO] Forcing extraction of the freshly downloaded archive.")

    if can_skip:
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

    try:
        previous_state = load_state()
        previous_structure = previous_state.get("validated_extracted_structure", [])
        previous_archive_top = set(previous_state.get("archive_top_structure", []))
        if previous_structure:
            for folder_name in previous_structure:
                if folder_name not in previous_archive_top:
                    continue
                folder_path = incoming_path / folder_name
                if folder_path.exists() and folder_path.is_dir():
                    shutil.rmtree(folder_path)
                    print(f"[INFO] Removed previous extracted folder: {folder_name}")

        extract_and_merge_zip(archive_file, incoming_path)
    except Exception as exc:
        mark_extraction_invalid(str(exc))
        raise

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
    try:
        archive_dir_relative = archive_file.parent.relative_to(incoming_path)
        archive_dir_name = str(archive_dir_relative)
    except ValueError:
        archive_dir_name = None
    if archive_dir_name:
        state["validated_extracted_structure"] = sorted(
            f for f in state.get("validated_extracted_structure", [])
            if f != archive_dir_name
        )
    save_state(state)

    if config.get("DELETE_ARCHIVE", "false").lower() == "true":
        archive_file.unlink()
        print("[INFO] Archive deleted after successful extraction.")


def verify_dataset():
    config = load_common_config("dataset")
    project_root = get_project_root()
    incoming = project_root / "incoming"

    source_type = (
        os.getenv("SOURCE_TYPE")
        or config.get("SOURCE_TYPE")
    )

    source_path = (
        os.getenv("SOURCE_PATH")
        or config.get("SOURCE_PATH")
    )

    output_filename = get_output_filename(
        source_type=source_type,
        source_path=source_path,
        config=config
    )

    if not is_archive_file(output_filename):

        print()
        print("=" * 60)
        print("DATASET VERIFICATION")
        print("=" * 60)
        print("[OK] Dataset verified successfully.")
        print("[OK] Dataset is ready for loading.")

        return

    archive_file = (
        project_root /
        config["DOWNLOAD_DIRECTORY"] /
        output_filename
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
