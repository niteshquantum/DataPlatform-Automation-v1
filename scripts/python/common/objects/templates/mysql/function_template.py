FUNCTION_TEMPLATE = """
CREATE FUNCTION {function_name}()
RETURNS INT
DETERMINISTIC
BEGIN
    RETURN (
        SELECT COUNT(*)
        FROM {table_name}
    );
END
""".strip()