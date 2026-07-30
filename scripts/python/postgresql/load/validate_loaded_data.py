from pathlib import Path
import sys
import psycopg2

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from scripts.python.common.config_loader import load_database_config

config = load_database_config("postgresql")

conn = psycopg2.connect(
    host=config["POSTGRESQL_HOST"],
    port=int(config["POSTGRESQL_PORT"]),
    user=config["POSTGRESQL_USER"],
    password=config["POSTGRESQL_PASSWORD"],
    dbname=config["POSTGRESQL_DB"]
)

cursor = conn.cursor()

cursor.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")

SYSTEM_OBJECTS = {
    "pg_stat_statements",
}

tables = [
    row[0]
    for row in cursor.fetchall()
    if row[0] not in SYSTEM_OBJECTS
]


print()
print("=" * 50)
print("LOADED DATA SUMMARY")
print("=" * 50)

for table in tables:

    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
    count = cursor.fetchone()[0]

    print(f"{table:<30} {count}")

cursor.close()
conn.close()

print("=" * 50)
print("DATA VALIDATION COMPLETED")
print("=" * 50)
