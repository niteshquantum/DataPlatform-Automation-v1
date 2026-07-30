from db_connection import get_db
 
db = get_db()
 
print()
print("=" * 50)
print("MONGODB VALIDATION")
print("=" * 50)
 
# Simple connectivity check -- this stage runs BEFORE schema_detector.py,
# so metadata/mongaodb/schema_registry.json does not exist yet.
# Detailed collection/document validation happens later, after load,
# in scripts/python/mongodb/load/validate_data.py.
db.command("ping")
 
print()
print(f"[OK] Connected to MongoDB database: {db.name}")
 
print()
print("=" * 50)
print("MONGODB VALIDATION SUCCESS")
print("=" * 50)
 
