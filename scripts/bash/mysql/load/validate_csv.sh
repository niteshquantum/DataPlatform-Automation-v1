#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING CSV FILES"
echo "====================================="
echo

cd "$PROJECT_ROOT"

python3 scripts/python/mysql/load/validate_csv.py

echo
echo "CSV VALIDATION SUCCESSFUL"
echo

exit 0