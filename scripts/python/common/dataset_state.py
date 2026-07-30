from pathlib import Path
import json
import hashlib
import zipfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]

STATE_DIR = ROOT / "metadata" / "common"
STATE_FILE = STATE_DIR / "dataset_state.json"


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _zip_top_folders(zip_path: Path):
    with zipfile.ZipFile(zip_path, "r") as zf:
        return sorted({Path(p).parts[0] for p in zf.namelist() if "/" in p or "\\" in p})


def load_state():
    if not STATE_FILE.exists():
        return {}
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state: dict):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def build_download_state(config: dict, archive_path: Path) -> dict:
    state = load_state()
    state["state_version"] = "1.0"
    state["dataset_identity"] = _sha256(archive_path)
    state["source_url"] = config.get("DATASET_URL", "")
    state["archive_filename"] = config.get("DATASET_NAME", "")
    state["archive_path"] = str(archive_path)
    state["archive_size_bytes"] = archive_path.stat().st_size
    state["archive_sha256"] = _sha256(archive_path)
    state["download_timestamp"] = _now_iso()
    state["download_status"] = "DOWNLOADED_VALID"
    return state


def build_extraction_state(config: dict, archive_path: Path, incoming_path: Path) -> dict:
    state = load_state()
    state["extraction_timestamp"] = _now_iso()
    state["extraction_status"] = "EXTRACTED_COMPLETE"
    state["archive_top_structure"] = _zip_top_folders(archive_path)
    state["validated_extracted_structure"] = sorted(
        str(p.relative_to(incoming_path))
        for p in incoming_path.iterdir()
        if p.is_dir()
    )
    state["force_extract"] = config.get("FORCE_EXTRACT", "false").lower() == "true"
    state["delete_archive"] = config.get("DELETE_ARCHIVE", "false").lower() == "true"
    return state


def mark_download_invalid(reason: str):
    state = load_state()
    state["download_status"] = "DOWNLOADED_INVALID"
    state["download_error"] = reason
    state["download_timestamp"] = _now_iso()
    save_state(state)


def mark_extraction_invalid(reason: str):
    state = load_state()
    state["extraction_status"] = "EXTRACTED_INVALID"
    state["extraction_error"] = reason
    state["extraction_timestamp"] = _now_iso()
    save_state(state)


def reset_state():
    if STATE_FILE.exists():
        STATE_FILE.unlink()
