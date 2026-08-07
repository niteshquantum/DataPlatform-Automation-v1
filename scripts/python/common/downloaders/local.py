import os
import shutil
from pathlib import Path

SOURCE_TYPE = "local"


def download(config, output_path):
    source_path = os.getenv("SOURCE_PATH")

    if source_path:
        source_path = source_path.strip()

    if not source_path:
        source_path = config.get("SOURCE_PATH")

    if not source_path:
        raise ValueError(
            "SOURCE_PATH is not configured."
        )

    source = Path(source_path)

    if not source.exists():
        raise FileNotFoundError(
            f"Local dataset not found: {source}"
        )

    destination = Path(output_path)

    if source.is_file():

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        target = destination

        if target.exists():
            action = "OVERWRITE"
            verb = "replaced"
        else:
            action = "NEW"
            verb = "copied"

        print()
        print(f"Source File : {source.name}")

        try:
            shutil.copy2(
                source,
                target
            )
        except Exception as exc:
            print(f"[{action}] FAILED")
            print(f"File   : {source.name}")
            print(f"Reason : {exc}")
            raise

        print(f"[{action}]")
        print(f"{source.name} {verb}.")

        return

    if source.is_dir():

        destination.mkdir(
            parents=True,
            exist_ok=True
        )

        new_count = 0
        overwrite_count = 0
        csv_count = 0
        json_count = 0

        print()
        print("Scanning local folder...")

        for file in source.iterdir():

            if (
                file.is_file()
                and file.suffix.lower() in (
                    ".csv",
                    ".json"
                )
            ):

                target = destination / file.name

                if target.exists():
                    action = "OVERWRITE"
                    verb = "replaced"
                    overwrite_count += 1
                else:
                    action = "NEW"
                    verb = "copied"
                    new_count += 1

                try:
                    shutil.copy2(
                        file,
                        target
                    )
                except Exception as exc:
                    print(f"[{action}] FAILED")
                    print(f"File   : {file.name}")
                    print(f"Reason : {exc}")
                    raise

                print(f"[{action}]")
                print(f"{file.name} {verb}.")

                if file.suffix.lower() == ".csv":
                    csv_count += 1

                if file.suffix.lower() == ".json":
                    json_count += 1

        total = new_count + overwrite_count

        if total == 0:
            raise ValueError(
                f"No CSV/JSON files found in: {source}"
            )

        print()
        print("Local Dataset Summary")
        print("---------------------")
        print(f"CSV Files              : {csv_count}")
        print(f"JSON Files             : {json_count}")
        print(f"Total Files            : {total}")
        print(f"Total Files Copied     : {new_count}")
        print(f"Total Files Overwritten: {overwrite_count}")
        print(f"Target Folder          : {destination}")

        return

    raise ValueError(
        f"Unsupported source: {source}"
    )
