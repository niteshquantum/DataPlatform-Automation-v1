import os
import sys
from pathlib import Path

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


def verify_incoming():
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

    output_filename = get_output_filename(
        source_type=source_type,
        source_path=source_path,
        config=config
    )

    archive = is_archive_file(output_filename)
    incoming = project_root / "incoming"

    if not archive:

        if not database:
            raise ValueError(
                "DATABASE is required for non-archive datasets."
            )

        target_dir = incoming / database.lower()

        if not target_dir.exists():
            raise FileNotFoundError(
                f"Incoming directory not found: {target_dir}"
            )

        files = list(target_dir.iterdir())

        if not files:
            raise RuntimeError(
                f"Incoming directory is empty: {target_dir}"
            )

        print()
        print("[OK] Incoming folder has downloaded files:")
        print(f"  Directory : {target_dir}")
        print(f"  Files     : {len(files)}")

        for f in sorted(files):
            print(f"    - {f.name}")

        return

    if incoming.exists() and any(incoming.iterdir()):

        folders = sorted(
            str(p.relative_to(incoming))
            for p in incoming.iterdir()
            if p.is_dir()
        )

        print()
        print("[OK] Incoming folder has extracted content:")
        print(f"  Directory : {incoming}")
        print(f"  Folders   : {len(folders)}")

        for folder in folders:
            print(f"    - {folder}")

    else:

        archive_file = (
            project_root /
            config["DOWNLOAD_DIRECTORY"] /
            output_filename
        )

        if archive_file.exists():
            print()
            print("[INFO] Archive exists but incoming folder is empty.")
            print("[INFO] Extraction may not have run yet.")
        else:
            raise FileNotFoundError(
                f"Archive not found: {archive_file}"
            )

    print()
    print("Incoming folder verification passed.")


def main():
    print()
    print("=" * 60)
    print("VERIFY INCOMING FOLDER")
    print("=" * 60)
    verify_incoming()


if __name__ == "__main__":
    main()