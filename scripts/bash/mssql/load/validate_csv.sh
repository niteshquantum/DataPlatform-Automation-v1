#!/bin/bash
set -e
source "$(dirname "$0")/../../common/set_project_root.sh"
cd "$PROJECT_ROOT"
python3 scripts/schema_detector.py mssql
python3 scripts/python/mssql/load/validate_csv.py
