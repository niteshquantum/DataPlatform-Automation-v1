# MSSQL TRIGGER template
#
# SQL Server triggers use CREATE OR ALTER TRIGGER (2017+).
# AFTER INSERT fires after the row is committed.
# Uses the logical INSERTED table for accessing new row data.
# GETDATE() is T-SQL equivalent of MySQL NOW().
# The trigger sets created_at on the inserted row via UPDATE.

TRIGGER_TEMPLATE = """
CREATE OR ALTER TRIGGER {trigger_name}
ON {table_name}
AFTER INSERT
AS
BEGIN
    SET NOCOUNT ON;

    UPDATE t
    SET t.created_at = GETDATE()
    FROM {table_name} t
    INNER JOIN INSERTED i ON t.created_at IS NULL;
END;
""".strip()
