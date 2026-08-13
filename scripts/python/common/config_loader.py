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


def load_source_config():

    if platform.system() == "Windows":
        config_file = ROOT / "config" / "windows" / "source.conf"
    else:
        config_file = ROOT / "config" / "ubuntu" / "source.conf"

    return load_config(config_file)


def get_migration_config_path(name):
    if platform.system() == "Windows":
        return ROOT / "config" / "windows" / "migration" / f"{name}.conf"
    else:
        return ROOT / "config" / "linux" / "migration" / f"{name}.conf"


def load_migration_config(database_name):
    return load_config(get_migration_config_path(database_name))


def load_migration_role_config(role):
    return load_config(get_migration_config_path(role))


def get_project_root():
    return ROOT