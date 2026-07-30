import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_loader import get_project_root
from template_loader import load_template
from object_utils import get_objects_config


def generate_views(database):

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
        / "views"
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(schema_registry, encoding="utf-8") as file:

        registry = json.load(file)

    config = get_objects_config()

    view_limit = config.get(
        "DEFAULT_VIEW_LIMIT",
        "10"
    )

    count = 1

    for table_name, columns in registry.items():

        view_name = f"v_{table_name}"

        #column_text = ",\n".join(columns)
        if database.lower() == "postgresql":
            column_text = ",\n".join(f'"{col}"' for col in columns)
        else:
            column_text = ",\n".join(columns)

        view_template = load_template(
            database,
            "view"
        )

        sql = view_template.format(

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