from pathlib import Path

from object_utils import project_root, read_json, write_json


DEFAULT_STRUCTURE = {
    "views": [],
    "functions": [],
    "procedures": [],
    "triggers": [],
    "events": [],
    "indexes": []
}


class ObjectRegistry:

    def __init__(self, database):

        self.registry_file = (
            project_root()
            / "metadata"
            / database
            / "object_registry.json"
        )

        if not self.registry_file.exists():

            write_json(
                self.registry_file,
                DEFAULT_STRUCTURE
            )

        self.data = read_json(self.registry_file)

    def load(self):

        return self.data

    def save(self):

        write_json(
            self.registry_file,
            self.data
        )