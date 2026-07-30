import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config_loader import get_project_root


RUNNER_PATHS = {
    "mysql": {
        "windows": "scripts/batch/mysql/setup/run_liquibase.bat",
        "linux": "scripts/bash/mysql/setup/run_liquibase.sh",
    },
    "postgresql": {
        "windows": "scripts/batch/postgresql/setup/run_liquibase.bat",
        "linux": "scripts/bash/postgresql/setup/run_liquibase.sh",
    },
    "mssql": {
        "windows": "scripts/batch/mssql/setup/run_liquibase.bat",
        "linux": "scripts/bash/mssql/setup/run_liquibase.sh",
    },
}


def deploy_objects(database):

    database = database.lower()

    root = get_project_root()

    if database not in RUNNER_PATHS:
        raise ValueError(
            f"Unsupported database for Liquibase object deployment: {database}"
        )

    changelog = (
        root
        / "liquibase"
        / database
        / "master_objects.xml"
    )

    if not changelog.exists():
        raise FileNotFoundError(
            f"Objects changelog not found: {changelog}"
        )

    # Path passed relative to project root because the existing
    # Liquibase runners execute from PROJECT_ROOT.
    relative_changelog = (
        changelog
        .relative_to(root)
        .as_posix()
    )

    system = platform.system().lower()

    if system == "windows":

        runner = (
            root
            / RUNNER_PATHS[database]["windows"]
        )

        changelog_argument = relative_changelog.replace("/", "\\")

        command = [
            str(runner),
            changelog_argument
        ]

    elif system == "linux":

        runner = (
            root
            / RUNNER_PATHS[database]["linux"]
        )

        command = [
            "bash",
            str(runner),
            relative_changelog
        ]

    else:

        raise RuntimeError(
            f"Unsupported operating system: {platform.system()}"
        )

    if not runner.exists():

        raise FileNotFoundError(
            f"Liquibase runner not found: {runner}"
        )

    print()
    print("=====================================")
    print("DATABASE OBJECT DEPLOYMENT")
    print("=====================================")
    print(f"Database  : {database}")
    print(f"OS        : {platform.system()}")
    print(f"Runner    : {runner}")
    print(f"Changelog : {relative_changelog}")
    print()

    subprocess.run(
        command,
        cwd=str(root),
        check=True
    )

    print()
    print("=====================================")
    print("DATABASE OBJECT DEPLOYMENT SUCCESSFUL")
    print("=====================================")


if __name__ == "__main__":

    if len(sys.argv) != 2:

        print(
            "Usage: deploy_objects.py <database>"
        )

        sys.exit(1)

    deploy_objects(
        sys.argv[1]
    )