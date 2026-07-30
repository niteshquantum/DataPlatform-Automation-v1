# MSSQL VIEW template
#
# Uses CREATE OR ALTER VIEW (SQL Server 2017+) — idempotent.
# Falls back to: DROP VIEW IF EXISTS + CREATE VIEW for older servers.
# Using CREATE OR ALTER which is the correct modern approach.
# TOP is used instead of LIMIT (T-SQL syntax).

VIEW_TEMPLATE = """
CREATE OR ALTER VIEW {view_name} AS

SELECT TOP ({limit})

{columns}

FROM {table_name};
""".strip()
