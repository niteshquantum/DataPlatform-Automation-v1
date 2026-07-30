import subprocess
import sys
from pathlib import Path
print("LOAD_ALL VERSION NEW 24-JUNE")
BASE_DIR = Path(__file__).resolve().parent
print("BASE_DIR =", BASE_DIR)
scripts = [
    "generate_dataset.py",
    "load_data.py"
]

for script in scripts:

    script_path = BASE_DIR / script

    print(f"Running {script}")

    subprocess.run(
        [sys.executable, str(script_path)],
        check=True
    )

print("Running schema_detector.py")

subprocess.run(
    [
        sys.executable,
        str(BASE_DIR.parents[2] / "scripts" / "schema_detector.py"),
        "mongodb"
    ],
    check=True
)

print("Running validate_data.py")

subprocess.run(
    [
        sys.executable,
        str(BASE_DIR / "validate_data.py")
    ],
    check=True
)

print("MongoDB Load Process Completed Successfully")