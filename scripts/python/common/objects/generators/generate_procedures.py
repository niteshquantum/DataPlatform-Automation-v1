import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_loader import get_project_root
from template_loader import load_template
from object_utils import get_objects_config


def generate_procedures(database):

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
        / "procedures"
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(schema_registry, encoding="utf-8") as file:
        registry = json.load(file)

    config = get_objects_config()

    prefix = config.get(
        "DEFAULT_PROCEDURE_PREFIX",
        "sp_"
    )

    limit = config.get(
        "DEFAULT_PROCEDURE_LIMIT",
        "100"
    )

    count = 1

    procedure_template = load_template(
        database,
        "procedure"
    )

    for table_name in registry.keys():

        procedure_name = f"{prefix}{table_name}"

        sql = procedure_template.format(
            procedure_name=procedure_name,
            table_name=table_name,
            limit=limit
        )

        filename = f"{count:03d}_{procedure_name}.sql"

        with open(
            output_folder / filename,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(sql)

        print(f"Generated : {filename}")

        count += 1