import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_loader import get_project_root
from template_loader import load_template
from object_utils import get_objects_config


def generate_indexes(database):

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
        / "indexes"
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(schema_registry, encoding="utf-8") as file:
        registry = json.load(file)

    config = get_objects_config()

    prefix = config.get(
        "DEFAULT_INDEX_PREFIX",
        "idx_"
    )

    count = 1

    index_template = load_template(
        database,
        "index"
    )

    for table_name, columns in registry.items():

        if not columns:
            continue

        first_column = columns[0]

# PostgreSQL ke liye mixed-case columns quote karo
        if database == "postgresql" and any(ch.isupper() for ch in first_column):
            sql_column = f'"{first_column}"'
        else:
            sql_column = first_column

        index_name = f"{prefix}{table_name}_{first_column}"

        sql = index_template.format(
            index_name=index_name,
            table_name=table_name,
            column=sql_column
        )

        filename = f"{count:03d}_{index_name}.sql"

        with open(
            output_folder / filename,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(sql)

        print(f"Generated : {filename}")

        count += 1