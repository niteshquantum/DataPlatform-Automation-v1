#!/bin/bash
set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo
echo "====================================="
echo "VALIDATE DESTINATION"
echo "====================================="
echo

python3 "$PROJECT_ROOT/scripts/python/migration/validate_destination.py"

echo
echo "DESTINATION VALIDATION COMPLETED"
echo

exit 0
