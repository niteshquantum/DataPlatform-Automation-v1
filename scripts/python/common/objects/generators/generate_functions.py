import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_loader import get_project_root
from template_loader import load_template
from object_utils import get_objects_config


def generate_functions(database):

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
        / "functions"
    )

    output_folder.mkdir(parents=True, exist_ok=True)

    with open(schema_registry, encoding="utf-8") as file:
        registry = json.load(file)

    config = get_objects_config()

    prefix = config.get("DEFAULT_FUNCTION_PREFIX", "fn_")

    count = 1

    function_template = load_template(
        database,
        "function"
    )

    for table_name in registry.keys():

        function_name = f"{prefix}{table_name}_count"

        sql = function_template.format(
            function_name=function_name,
            table_name=table_name
        )

        filename = f"{count:03d}_{function_name}.sql"

        with open(
            output_folder / filename,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(sql)

        print(f"Generated : {filename}")

        count += 1