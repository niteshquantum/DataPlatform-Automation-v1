from pathlib import Path
import pandas as pd
from db_connection import get_db

db = get_db()

ROOT_DIR = Path(__file__).resolve().parents[3]
DATASET_DIR = ROOT_DIR / "datasets" / "mongodb"

collections = [
    "customers",
    "sellers",
    "products",
    "orders",
    "orderdetails"
]

for collection in collections:

    file_path = DATASET_DIR / f"{collection}.csv"

    if not file_path.exists():
        print(f"{collection}.csv not found")
        continue

    print(f"Loading {file_path}")

    df = pd.read_csv(file_path)

    records = df.to_dict("records")

    if db[collection].count_documents({}) == 0:

        if records:
            db[collection].insert_many(records)

        print(f"{collection} data loaded.")

    else:

        print(f"{collection} already contains data.")

print("Data loading completed.")