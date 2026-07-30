# PostgreSQL FUNCTION template
#
# PostgreSQL functions use $$ dollar-quoting instead of BEGIN/END with DELIMITER.
# RETURNS INTEGER is the correct keyword (not INT in standard PG style).
# LANGUAGE plpgsql is required.
# CREATE OR REPLACE is idempotent.

FUNCTION_TEMPLATE = """
CREATE OR REPLACE FUNCTION {function_name}()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN (
        SELECT COUNT(*)::INTEGER
        FROM {table_name}
    );
END;
$$;
""".strip()
