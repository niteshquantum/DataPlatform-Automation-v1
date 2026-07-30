PROCEDURE_TEMPLATE = """
CREATE PROCEDURE {procedure_name}()
BEGIN
    SELECT *
    FROM {table_name}
    LIMIT {limit};
END
""".strip()