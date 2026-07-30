# MSSQL FUNCTION (scalar) template
#
# SQL Server scalar functions use CREATE OR ALTER FUNCTION (2017+).
# Must specify SCHEMABINDING or not — omitting for flexibility.
# RETURNS INT, uses SELECT COUNT(*) within function body.
# SET NOCOUNT ON prevents extra result sets.

FUNCTION_TEMPLATE = """
CREATE OR ALTER FUNCTION {function_name}()
RETURNS INT
AS
BEGIN
    DECLARE @count INT;
    SELECT @count = COUNT(*) FROM {table_name};
    RETURN @count;
END;
""".strip()
