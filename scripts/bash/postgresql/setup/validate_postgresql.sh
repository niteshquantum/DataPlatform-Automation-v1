#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING POSTGRESQL"
echo "====================================="
echo

python3 "$PROJECT_ROOT/scripts/python/postgresql/setup/validate_postgresql.py"

echo
echo "====================================="
echo "POSTGRESQL VALIDATED"
echo "====================================="
echo

exit 0