
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

steps = [
    [sys.executable, str(ROOT / "scripts" / "python" / "mongodb" / "setup" / "create_collections.py")],
    [sys.executable, str(ROOT / "scripts" / "python" / "mongodb" / "setup" / "create_indexes.py")],
    [sys.executable, str(ROOT / "scripts" / "schema_detector.py"), "mongodb"],
    [sys.executable, str(ROOT / "scripts" / "data_loader_mongodb.py")],
    [sys.executable, str(ROOT / "scripts" / "python" / "mongodb" / "load" / "validate_data.py")],
]

for step in steps:
    print(f"Running {' '.join(step)}")
    subprocess.run(step, cwd=str(ROOT), check=True)

print("MongoDB Load Process Completed Successfully")
