from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_loader import get_project_root
from config_loader import load_config


def project_root():
    return get_project_root()


def ensure_directory(path):
    Path(path).mkdir(
        parents=True,
        exist_ok=True
    )


def read_json(path):

    path = Path(path)

    if not path.exists():
        return {}

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


def write_json(path, data):

    ensure_directory(
        Path(path).parent
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4
        )


def get_objects_config():

    config_file = (
        project_root()
        / "config"
        / "common"
        / "objects.conf"
    )

    return load_config(
        config_file
    )