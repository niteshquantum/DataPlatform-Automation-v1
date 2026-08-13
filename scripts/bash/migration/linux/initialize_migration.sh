#!/bin/bash
set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo
echo "====================================="
echo "INITIALIZE MIGRATION"
echo "====================================="
echo

python3 "$PROJECT_ROOT/scripts/python/migration/initialize.py"

echo
echo "MIGRATION INITIALIZATION COMPLETED"
echo

exit 0
