from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parents[3]


def load_config(config_path):
    config = {}

    with open(config_path, "r") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            if "=" in line:
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip().strip('"')

    return config


def load_database_config(database_name):

    if platform.system() == "Windows":
        config_file = (
            ROOT /
            "config" /
            "windows" /
            f"{database_name}.conf"
        )
    else:
        config_file = (
            ROOT /
            "config" /
            "ubuntu" /
            f"{database_name}.conf"
        )

    return load_config(config_file)


def load_common_config(config_name):

    config_file = (
        ROOT /
        "config" /
        "common" /
        f"{config_name}.conf"
    )

    return load_config(config_file)


def get_project_root():
    return ROOT