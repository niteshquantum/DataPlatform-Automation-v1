#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING LOADED DATA"
echo "====================================="
echo

cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
python3 scripts/python/postgresql/load/validate_loaded_data.py

echo
echo "LOADED DATA VALIDATION SUCCESSFUL"
echo

exit 0