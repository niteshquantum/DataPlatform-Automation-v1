from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.mongodb.setup.db_connection import get_db  # noqa: E402


def collection_names():
    registry_path = ROOT / "metadata" / "mongodb" / "schema_registry.json"

    if registry_path.exists():
        with open(registry_path, encoding="utf-8") as registry_file:
            registry = json.load(registry_file)
        return sorted(registry)

    archive_dir = ROOT / "archive" / "mongodb"
    names = {
        path.stem.strip().lower().replace(" ", "_")
        for pattern in ("*.csv", "*.json")
        for path in archive_dir.glob(pattern)
    }
    return sorted(names)


def main():
    db = get_db()
    existing = set(db.list_collection_names())

    print("=" * 50)
    print("MONGODB COLLECTION CREATION")
    print("=" * 50)

    for name in collection_names():
        if name in existing:
            print(f"[OK] Collection already exists: {name}")
            continue
        db.create_collection(name)
        print(f"[OK] Collection created: {name}")

    print("=" * 50)
    print("MONGODB COLLECTION CREATION COMPLETED")
    print("=" * 50)


if __name__ == "__main__":
    main()
