# MSSQL INDEX template
#
# CREATE INDEX IF NOT EXISTS equivalent in T-SQL:
# SQL Server does not support IF NOT EXISTS in CREATE INDEX directly.
# Use the idiomatic pattern: check sys.indexes before creating.
# Using DROP/CREATE pair inside an IF block is the safe approach.
# Note: Liquibase's <createIndex> handles idempotency automatically,
# but this template is for direct SQL generation.

INDEX_TEMPLATE = """
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = N'{index_name}'
      AND object_id = OBJECT_ID(N'{table_name}')
)
BEGIN
    CREATE INDEX {index_name}
    ON {table_name} ({column});
END;
""".strip()
