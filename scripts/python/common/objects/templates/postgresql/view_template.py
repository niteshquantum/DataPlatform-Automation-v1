# PostgreSQL VIEW template
#
# Uses CREATE OR REPLACE VIEW — idempotent on rerun.
# LIMIT syntax is identical to MySQL.

VIEW_TEMPLATE = """
CREATE OR REPLACE VIEW {view_name} AS

SELECT

{columns}

FROM {table_name}

LIMIT {limit};
""".strip()
