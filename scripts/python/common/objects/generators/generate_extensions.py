"""
Generator for PostgreSQL extensions.

Extensions are PostgreSQL-specific — MySQL and MSSQL have no equivalent concept.

This generator creates a fixed set of safe, commonly-used PostgreSQL extensions.
Extensions are database-level objects (not schema-specific) so they do not need
to iterate over schema_registry.json.

Safe extensions used:
  - pg_stat_statements : query statistics (commonly pre-installed)
  - uuid-ossp          : UUID generation functions
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_loader import get_project_root
from template_loader import load_template


# Safe, commonly available PostgreSQL extensions for bootstrap demonstration.
# These are broadly available and will not break if already installed (IF NOT EXISTS).
BOOTSTRAP_EXTENSIONS = [
    "pg_stat_statements",
    "uuid-ossp",
]


def generate_extensions(database):

    root = get_project_root()

    output_folder = (
        root
        / "objects"
        / database
        / "generated"
        / "extensions"
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    extension_template = load_template(
        database,
        "extension"
    )

    count = 1

    for extension_name in BOOTSTRAP_EXTENSIONS:

        sql = extension_template.format(
            extension_name=extension_name
        )

        # Sanitize filename: uuid-ossp -> uuid_ossp
        safe_name = extension_name.replace("-", "_")
        filename = f"{count:03d}_{safe_name}.sql"

        with open(
            output_folder / filename,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(sql)

        print(f"Generated : {filename}")

        count += 1
