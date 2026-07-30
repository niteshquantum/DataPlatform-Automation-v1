# PostgreSQL PROCEDURE template
#
# PostgreSQL procedures (CREATE PROCEDURE) require PostgreSQL 11+.
# They use $$ dollar-quoting and LANGUAGE plpgsql.
# Procedures do not return a value (use OUT parameters or INOUT for output).
# CREATE OR REPLACE PROCEDURE is supported from PostgreSQL 14+.
# Using CREATE OR REPLACE for idempotency.

PROCEDURE_TEMPLATE = """
CREATE OR REPLACE PROCEDURE {procedure_name}()
LANGUAGE plpgsql
AS $$
BEGIN
    -- Generated bootstrap procedure for {table_name}
    -- Performs a read-only scan to verify table accessibility.
    PERFORM COUNT(*) FROM {table_name};
END;
$$;
""".strip()
