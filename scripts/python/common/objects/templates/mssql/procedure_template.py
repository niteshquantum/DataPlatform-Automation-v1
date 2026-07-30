# MSSQL STORED PROCEDURE template
#
# SQL Server stored procedures use CREATE OR ALTER PROCEDURE (2016 SP1+).
# SET NOCOUNT ON suppresses row-count messages.
# SELECT TOP with limit — T-SQL syntax.

PROCEDURE_TEMPLATE = """
CREATE OR ALTER PROCEDURE {procedure_name}
AS
BEGIN
    SET NOCOUNT ON;

    SELECT TOP ({limit}) *
    FROM {table_name};
END;
""".strip()
