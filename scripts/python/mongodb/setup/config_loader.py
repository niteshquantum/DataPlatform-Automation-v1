from pathlib import Path
import platform

ROOT = Path(__file__).resolve().parents[4]

if platform.system() == "Windows":
    CONFIG_FILE = ROOT / "config" / "windows" / "mongodb.conf"
else:
    CONFIG_FILE = ROOT / "config" / "ubuntu" / "mongodb.conf"


def load_config():

    config = {}

    with open(CONFIG_FILE, encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if line and "=" in line:

                key, value = line.split("=", 1)

                config[key.strip()] = value.strip()

    return config