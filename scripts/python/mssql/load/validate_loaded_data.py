from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.mssql.setup.db_connection import get_connection

conn = get_connection()

cursor = conn.cursor()

cursor.execute("""
    SELECT TABLE_NAME
    FROM INFORMATION_SCHEMA.TABLES
    WHERE TABLE_CATALOG = DB_NAME()
      AND TABLE_TYPE = 'BASE TABLE'
""")

tables = [row[0] for row in cursor.fetchall()]

system_tables = {
    "databasechangelog",
    "databasechangeloglock"
}

print()
print("=" * 50)
print("LOADED DATA SUMMARY")
print("=" * 50)

for table in sorted(tables):

    if table.lower() in system_tables:
        continue

    cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
    count = cursor.fetchone()[0]

    print(f"{table:<30} {count}")

cursor.close()
conn.close()

print("=" * 50)
print("DATA VALIDATION COMPLETED")
print("=" * 50)