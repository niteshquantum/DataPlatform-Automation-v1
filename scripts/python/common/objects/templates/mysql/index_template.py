INDEX_TEMPLATE = """
CREATE INDEX {index_name}

ON {table_name}

({column});
""".strip()