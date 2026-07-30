import importlib
import sys
from pathlib import Path

#sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent)
)

from config_loader import get_project_root
from database_capabilities import get_supported_objects


def _load_master_template(database):
    """Load the Liquibase master template for the given database dynamically."""
    module = importlib.import_module(
        f"templates.{database}.liquibase_master_template"
    )
    return (
        module.MASTER_HEADER,
        module.MASTER_INCLUDE,
        module.MASTER_FOOTER,
    )



def generate_master_objects(database):

    root = get_project_root()

    master_header, master_include, master_footer = _load_master_template(database)

    liquibase_root = (
        root
        / "liquibase"
        / database
    )

    master_file = (
        liquibase_root
        / "master_objects.xml"
    )

    xml = master_header

    sources = [
        "generated",
        "custom"
    ]

    include_count = 0

    for source in sources:

        object_root = (
            liquibase_root
            / "objects"
            / source
        )

        if not object_root.exists():
            continue

        for object_type in get_supported_objects(database):

            folder = (
                object_root
                / object_type
            )

            if not folder.exists():
                continue

            files = sorted(
                folder.glob("*.xml")
            )

            for file in files:

                include = (
                    f"objects/"
                    f"{source}/"
                    f"{object_type}/"
                    f"{file.name}"
                )

                xml += master_include.format(
                    file=include
                )

                include_count += 1

    xml += master_footer

    master_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        master_file,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(xml)

    print(
        f"Generated : {master_file.name}"
    )

    print(
        f"Liquibase includes : {include_count}"
    )


if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage : generate_master_objects.py <database>"
        )

        sys.exit(1)

    generate_master_objects(
        sys.argv[1]
    )