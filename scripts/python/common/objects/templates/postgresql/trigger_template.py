# PostgreSQL TRIGGER template
#
# PostgreSQL triggers require a TRIGGER FUNCTION (returns TRIGGER type).
# The trigger function is created first, then the trigger references it.
# CREATE OR REPLACE FUNCTION is idempotent.
# DROP TRIGGER IF EXISTS + CREATE TRIGGER ensures idempotent trigger creation.
# FOR EACH ROW BEFORE INSERT sets created_at timestamp on insert.

TRIGGER_TEMPLATE = """
CREATE OR REPLACE FUNCTION {trigger_name}_fn()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.created_at := NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS {trigger_name} ON {table_name};

CREATE TRIGGER {trigger_name}
BEFORE INSERT
ON {table_name}
FOR EACH ROW
EXECUTE FUNCTION {trigger_name}_fn();
""".strip()
