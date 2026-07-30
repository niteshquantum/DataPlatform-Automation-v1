# PostgreSQL MATERIALIZED VIEW template
#
# PostgreSQL-specific — MySQL has no materialized views.
# CREATE MATERIALIZED VIEW IF NOT EXISTS is supported from PostgreSQL 9.3+.
# WITH NO DATA defers population — safe for bootstrap/demo objects.
# REFRESH MATERIALIZED VIEW can be called separately to populate.

MATERIALIZED_VIEW_TEMPLATE = """
CREATE MATERIALIZED VIEW IF NOT EXISTS {view_name} AS

SELECT

{columns}

FROM {table_name}

WITH NO DATA;
""".strip()
