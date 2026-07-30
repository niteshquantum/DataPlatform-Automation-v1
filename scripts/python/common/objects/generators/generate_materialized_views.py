"""
Generator for PostgreSQL materialized views.

Materialized views are PostgreSQL-specific — they are not supported
in MySQL or MSSQL in this project.

Generated materialized views are created with WITH NO DATA to avoid
data population at creation time. A REFRESH MATERIALIZED VIEW can be
scheduled or run separately.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_loader import get_project_root
from template_loader import load_template
from object_utils import get_objects_config


def generate_materialized_views(database):

    root = get_project_root()

    schema_registry = (
        root
        / "metadata"
        / database
        / "schema_registry.json"
    )

    output_folder = (
        root
        / "objects"
        / database
        / "generated"
        / "materialized_views"
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    if not schema_registry.exists():
        print(
            f"Schema registry not found, skipping "
            f"materialized view generation: {schema_registry}"
        )
        return

    with open(schema_registry, encoding="utf-8") as file:
        registry = json.load(file)

    config = get_objects_config()

    view_limit = config.get(
        "DEFAULT_VIEW_LIMIT",
        "10"
    )

    count = 1

    for table_name, columns in registry.items():

        # Use mv_ prefix to distinguish from regular views
        view_name = f"mv_{table_name}"

        if database == "postgresql":
            formatted_columns = []

            for col in columns:
                if any(ch.isupper() for ch in col):
                    formatted_columns.append(f'"{col}"')
                else:
                    formatted_columns.append(col)

            column_text = ",\n".join(formatted_columns)
        else:
            column_text = ",\n".join(columns)

        materialized_view_template = load_template(
            database,
            "materialized_view"
        )

        sql = materialized_view_template.format(
            view_name=view_name,
            table_name=table_name,
            columns=column_text,
            limit=view_limit
        )

        filename = f"{count:03d}_{view_name}.sql"

        with open(
            output_folder / filename,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(sql)

        print(f"Generated : {filename}")

        count += 1
