import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_loader import get_project_root
from object_registry import ObjectRegistry


class ObjectDetector:

    def __init__(self, database):

        self.database = database

        self.project_root = get_project_root()

        self.schema_registry = (
            self.project_root
            / "metadata"
            / database
            / "schema_registry.json"
        )

        self.registry = ObjectRegistry(database)

    def detect(self):

        print(f"Detecting objects for {self.database}...")

        # TODO
        # Read schema_registry.json
        # Generate object registry

        self.registry.save()


if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage : object_detector.py <database>")
        sys.exit(1)

    detector = ObjectDetector(sys.argv[1])

    detector.detect()