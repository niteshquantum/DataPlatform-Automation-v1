# PostgreSQL EXTENSION template
#
# PostgreSQL-specific — MySQL/MSSQL have no extensions concept.
# CREATE EXTENSION IF NOT EXISTS is idempotent.
# This template is used for bootstrap/demo extension registration.
# The extension_name is provided by the generator.

EXTENSION_TEMPLATE = """
CREATE EXTENSION IF NOT EXISTS "{extension_name}";
""".strip()
