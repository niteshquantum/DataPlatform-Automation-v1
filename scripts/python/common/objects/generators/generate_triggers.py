import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_loader import get_project_root
from template_loader import load_template
from object_utils import get_objects_config


def generate_triggers(database):

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
        / "triggers"
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(schema_registry, encoding="utf-8") as file:
        registry = json.load(file)

    config = get_objects_config()

    prefix = config.get(
        "DEFAULT_TRIGGER_PREFIX",
        "trg_"
    )

    count = 1

    skipped = []

    trigger_template = load_template(
        database,
        "trigger"
    )

    for table_name, columns in registry.items():

        normalized_columns = {
            column.strip().lower()
            for column in columns
        }

        if "created_at" not in normalized_columns:

            print(
                f"Skipped trigger for {table_name}: "
                "created_at column not found"
            )

            skipped.append(
                {
                    "table": table_name,
                    "reason": "created_at column not found",
                }
            )

            continue

        trigger_name = (
            f"{prefix}{table_name}_before_insert"
        )

        sql = trigger_template.format(

            trigger_name=trigger_name,

            table_name=table_name

        )

        filename = (
            f"{count:03d}_{trigger_name}.sql"
        )

        with open(
            output_folder / filename,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(sql)

        print(f"Generated : {filename}")

        count += 1

    report = {
        "database": database,
        "generated": count - 1,
        "skipped": skipped,
        "status": "complete",
    }

    root = get_project_root()
    report_path = (
        root / "metadata" / database / "trigger_generation_report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)