#!/bin/bash
set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo
echo "====================================="
echo "EXTRACT SOURCE SCHEMA"
echo "====================================="
echo

python3 "$PROJECT_ROOT/scripts/python/migration/extract_schema.py"

echo
echo "SOURCE SCHEMA EXTRACTION COMPLETED"
echo

exit 0
