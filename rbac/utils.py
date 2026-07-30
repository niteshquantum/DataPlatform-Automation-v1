import json
from pathlib import Path
import hashlib

RBAC_DIR = Path(__file__).resolve().parent


def load_json(filename):
    """
    Load JSON file from RBAC directory.
    """

    file_path = RBAC_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(f"RBAC file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
    



def hash_password(password):
    """
    Generate SHA256 hash.
    """

    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def verify_password(password, stored_hash):
    """
    Verify password.
    """

    return hash_password(password) == stored_hash