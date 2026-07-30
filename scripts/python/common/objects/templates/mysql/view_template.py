VIEW_TEMPLATE = """
CREATE OR REPLACE VIEW {view_name} AS

SELECT

{columns}

FROM {table_name}

LIMIT {limit};
""".strip()