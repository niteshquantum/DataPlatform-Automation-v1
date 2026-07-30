from pathlib import Path
import sys
import tempfile
import zipfile

import gdown

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import (
    load_common_config,
    get_project_root
)
from scripts.python.common.dataset_state import (
    build_download_state,
    mark_download_invalid,
    reset_state,
    save_state
)


def print_header():
    print()
    print("=" * 60)
    print("DATASET DOWNLOAD")
    print("=" * 60)


def create_directory(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)


def validate_zip(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Downloaded archive not found: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"Downloaded archive is empty: {path}")
    try:
        with zipfile.ZipFile(path, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                raise ValueError(f"Corrupt entry in ZIP: {bad}")
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Invalid ZIP file: {path}") from exc


def download_dataset():

    config = load_common_config("dataset")

    project_root = get_project_root()

    download_directory = (
        project_root /
        config["DOWNLOAD_DIRECTORY"]
    )

    create_directory(download_directory)

    output_file = (
        download_directory /
        config["DATASET_NAME"]
    )

    force = config.get("FORCE_DOWNLOAD", "false").lower() == "true"

    if output_file.exists() and not force:
        print()
        print("[INFO] Dataset already exists:")
        print(output_file)
        try:
            validate_zip(output_file)
            print("[INFO] Existing archive is valid. Skipping download.")
            return output_file
        except Exception as exc:
            print()
            print(f"[WARNING] Existing archive invalid: {exc}")
            print("[INFO] Will re-download.")

    print()
    print("Downloading dataset...")
    print()

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=download_directory,
            delete=False,
            suffix=".tmp"
        ) as tmp:
            tmp_path = Path(tmp.name)

        gdown.download(
            config["DATASET_URL"],
            str(tmp_path),
            quiet=False
        )

        validate_zip(tmp_path)

        tmp_path.replace(output_file)

        state = build_download_state(config, output_file)
        save_state(state)

        print()
        print("[SUCCESS] Dataset downloaded successfully.")
        print(output_file)

        return output_file

    except Exception:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)
        if output_file.exists():
            try:
                validate_zip(output_file)
            except Exception:
                output_file.unlink(missing_ok=True)
        raise


def main():
    print_header()
    download_dataset()


if __name__ == "__main__":
    main()
