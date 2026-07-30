from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.mongodb.setup.db_connection import get_db  # noqa: E402


def main():
    db = get_db()

    print("=" * 50)
    print("MONGODB INDEX VALIDATION")
    print("=" * 50)
    print("No custom MongoDB indexes are defined by the current repository.")
    print("Validating MongoDB default _id indexes for existing collections.")

    for collection_name in sorted(db.list_collection_names()):
        index_names = [
            index["name"]
            for index in db[collection_name].list_indexes()
        ]

        if "_id_" not in index_names:
            raise RuntimeError(
                f"Default _id index missing for collection: {collection_name}"
            )

        print(f"[OK] {collection_name}: _id_")

    print("=" * 50)
    print("MONGODB INDEX VALIDATION COMPLETED")
    print("=" * 50)


if __name__ == "__main__":
    main()
