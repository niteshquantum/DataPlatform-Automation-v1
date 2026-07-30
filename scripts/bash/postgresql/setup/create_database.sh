#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "CREATE DATABASE"
echo "====================================="
echo

python3 "$PROJECT_ROOT/scripts/python/postgresql/setup/create_database.py"

echo
echo "DATABASE READY"
echo

exit 0