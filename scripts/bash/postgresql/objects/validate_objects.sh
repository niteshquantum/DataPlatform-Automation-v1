#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo
echo "====================================="
echo "POSTGRESQL OBJECTS VALIDATION"
echo "====================================="
echo

python3 scripts/python/common/objects/validate_objects.py postgresql

echo
echo "====================================="
echo "POSTGRESQL OBJECTS VALIDATION SUCCESSFUL"
echo "====================================="
echo

exit 0
