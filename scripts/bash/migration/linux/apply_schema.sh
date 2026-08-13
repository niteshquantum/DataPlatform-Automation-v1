#!/bin/bash
set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo
echo "====================================="
echo "APPLY SCHEMA"
echo "====================================="
echo

python3 "$PROJECT_ROOT/scripts/python/migration/apply_schema.py"

echo.
echo "SCHEMA APPLICATION COMPLETED"
echo.

exit 0
