from pathlib import Path
import shutil
import subprocess
import zipfile
import os
import threading
import time

def get_7zip_executable() -> Path:
    """
    Returns the path to the 7-Zip executable.

    Priority:
    1. 7z available in PATH.
    2. Default Windows installation path.

    Raises:
        FileNotFoundError if 7-Zip is not found.
    """

    executable = shutil.which("7z")

    if executable:
        return Path(executable)

    if os.name == "nt":
        default_path = Path(r"C:\Program Files\7-Zip\7z.exe")

        if default_path.exists():
            return default_path

    raise FileNotFoundError(
        "7-Zip executable not found. "
        "Run the platform-specific install_7zip script before downloading datasets."
    )

def has_7zip() -> bool:
    """
    Returns True if 7-Zip is available.
    """

    try:
        get_7zip_executable()
        return True
    except FileNotFoundError:
        return False

    

def _has_data_files(names: list) -> bool:
    return any(
        name.lower().endswith((".csv", ".json"))
        for name in names
    )


def _has_data_files_7z(listing: str) -> bool:
    for line in listing.splitlines():
        parts = line.split()
        if len(parts) < 6:
            continue
        path = " ".join(parts[5:]).replace("\\", "/")
        if path.lower().endswith((".csv", ".json")):
            return True
    return False


def validate_archive(archive_path: Path) -> None:
    """
    Validates a ZIP archive.

    First tries Python's zipfile module.
    If the archive uses an unsupported compression method
    (e.g. Deflate64), automatically falls back to 7-Zip.

    Validation includes:
    - ZIP structural integrity (testzip)
    - Presence of at least one supported data file (.csv or .json)
    """

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            if not _has_data_files(zf.namelist()):
                raise ValueError(
                    "Archive contains no supported data files (.csv or .json)"
                )

            bad = zf.testzip()

            if bad is not None:
                raise ValueError(f"Corrupt archive entry: {bad}")

    except NotImplementedError:

        exe = get_7zip_executable()

        result = subprocess.run(
            [
                str(exe),
                "t",
                str(archive_path)
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise ValueError(
                "Archive validation failed.\n"
                f"{result.stderr}"
            )

        list_result = subprocess.run(
            [
                str(exe),
                "l",
                str(archive_path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if list_result.returncode != 0:
            raise ValueError(
                "Archive content listing failed.\n"
                f"{list_result.stderr}"
            )

        if not _has_data_files_7z(list_result.stdout):
            raise ValueError(
                "Archive contains no supported data files (.csv or .json)"
            )

def extract_archive(archive_path: Path, destination: Path) -> None:
    """
    Extracts a ZIP archive.

    Uses Python zipfile by default.
    Automatically falls back to 7-Zip for unsupported
    compression methods (e.g. Deflate64).
    """

    destination.mkdir(parents=True, exist_ok=True)

    try:

        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(destination)

    except NotImplementedError:


        exe = get_7zip_executable()

        print("[INFO] Extraction started...", flush=True)
        print("[INFO] Large archives may take several minutes.", flush=True)

        process = subprocess.Popen(
            [
                str(exe),
                "x",
                str(archive_path),
                f"-o{destination}",
                "-y"
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True
        )


        def heartbeat():

            elapsed = 0

            while process.poll() is None:

                for _ in range(20):

                    if process.poll() is not None:
                        return

                    time.sleep(1)

                elapsed += 20

                if process.poll() is None:

                    minutes = elapsed // 60
                    seconds = elapsed % 60

                    print(
                        f"[INFO] Extraction in progress... ({minutes:02}:{seconds:02})", flush=True
                    )


        heartbeat_thread = threading.Thread(
            target=heartbeat,
            daemon=True
        )

        heartbeat_thread.start()

        _, stderr = process.communicate()

        heartbeat_thread.join()

        if process.returncode != 0:

            raise RuntimeError(
                "Archive extraction failed.\n"
                f"{stderr}"
            )

def list_archive_folders(archive_path: Path) -> list[str]:
    """
    Returns the list of top-level folders in the archive.

    Uses Python zipfile by default.
    Falls back to 7-Zip when Python cannot read the archive.
    """

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            return sorted({
                Path(name).parts[0]
                for name in zf.namelist()
                if "/" in name or "\\" in name
            })

    except NotImplementedError:

        exe = get_7zip_executable()

        result = subprocess.run(
            [
                str(exe),
                "l",
                str(archive_path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        folders = set()

        for line in result.stdout.splitlines():

            parts = line.split()

            if len(parts) < 6:
                continue

            path = " ".join(parts[5:]).replace("\\", "/")

            if "/" not in path:
                continue

            folders.add(path.split("/")[0])

        return sorted(folders)