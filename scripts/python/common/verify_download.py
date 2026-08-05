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


def verify_download():
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

    if archive:

        download_dir = project_root / config["DOWNLOAD_DIRECTORY"]
        download_file = download_dir / output_filename

        if not download_file.exists():
            raise FileNotFoundError(
                f"Downloaded archive not found: {download_file}"
            )

        print()
        print("[OK] Downloaded archive found:")
        print(f"  File : {download_file}")
        print(f"  Size : {download_file.stat().st_size / (1024 * 1024):.2f} MB")

    else:

        if not database:
            raise ValueError(
                "DATABASE is required for non-archive datasets."
            )

        incoming_dir = project_root / "incoming" / database.lower()

        if not incoming_dir.exists():
            raise FileNotFoundError(
                f"Incoming directory not found: {incoming_dir}"
            )

        files = list(incoming_dir.iterdir())

        if not files:
            raise RuntimeError(
                f"No files found in incoming directory: {incoming_dir}"
            )

        print()
        print("[OK] Downloaded files found:")
        print(f"  Directory : {incoming_dir}")
        print(f"  Files     : {len(files)}")

        for f in sorted(files):
            print(f"    - {f.name}")

    print()
    print("Download verification passed.")


def main():
    print()
    print("=" * 60)
    print("VERIFY DOWNLOAD")
    print("=" * 60)
    verify_download()


if __name__ == "__main__":
    main()