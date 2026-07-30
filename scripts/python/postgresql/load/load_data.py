#!/usr/bin/env python

"""
PostgreSQL Data Load Wrapper

Calls the generic data loader for PostgreSQL.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]

sys.path.insert(0, str(ROOT / "scripts"))

from data_loader import main


if __name__ == "__main__":
    sys.argv = ["data_loader.py", "postgresql"]
    main()