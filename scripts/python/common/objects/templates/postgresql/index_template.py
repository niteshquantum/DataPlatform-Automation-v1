# PostgreSQL INDEX template
#
# CREATE INDEX IF NOT EXISTS is idempotent (PostgreSQL 9.5+).
# Syntax is compatible with MySQL: CREATE INDEX ... ON table (column).

INDEX_TEMPLATE = """
CREATE INDEX IF NOT EXISTS {index_name}

ON {table_name}

({column});
""".strip()
