#!/bin/bash
set -e
source "$(dirname "$0")/../../common/set_project_root.sh"
cd "$PROJECT_ROOT"
if [ "${SCHEMA_SOURCE}" = "DATABASE" ]; then
    python3 scripts/schema_extractor.py mssql
else
    python3 scripts/schema_detector.py mssql
fi
python3 scripts/python/mssql/load/validate_csv.py
