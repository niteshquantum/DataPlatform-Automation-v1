#!/bin/bash
set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo
echo "====================================="
echo "GENERATE TARGET DDL"
echo "====================================="
echo

python3 "$PROJECT_ROOT/scripts/python/migration/generate_ddl.py"

echo
echo "TARGET DDL GENERATION COMPLETED"
echo

exit 0
