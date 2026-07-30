import json
from pathlib import Path
import sys

#sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent)
)

from config_loader import get_project_root


class DatabaseCapabilities:

    def __init__(self):

        self.project_root = get_project_root()

        self.config_file = (
            self.project_root
            / "config"
            / "common"
            / "database_objects.json"
        )

        with open(
            self.config_file,
            encoding="utf-8"
        ) as file:

            self.database_objects = json.load(file)

    def get_supported_objects(
        self,
        database
    ):

        return self.database_objects.get(
            database.lower(),
            []
        )

    def supports(
        self,
        database,
        object_name
    ):

        return (
            object_name
            in self.get_supported_objects(database)
        )


_capability = DatabaseCapabilities()


def get_supported_objects(database):

    return _capability.get_supported_objects(database)


def supports_object(
    database,
    object_name
):

    return _capability.supports(
        database,
        object_name
    )