#!/bin/bash

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING LOADED DATA"
echo "====================================="
echo

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

cd "$PROJECT_ROOT"

python3 scripts/python/mongodb/load/validate_loaded_data.py

echo
echo "LOADED DATA VALIDATION SUCCESSFUL"
echo
echo "====================================="
echo