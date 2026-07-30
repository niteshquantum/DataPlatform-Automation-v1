from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.mongodb.setup.db_connection import get_db


db = get_db()

collections = db.list_collection_names()

print()
print("=" * 50)
print("LOADED DATA SUMMARY")
print("=" * 50)

if not collections:

    print("No collections found.")

else:

    for collection in sorted(collections):

        count = db[collection].count_documents({})

        print(f"{collection:<30} {count}")

print("=" * 50)
print("DATA VALIDATION COMPLETED")
print("=" * 50)
