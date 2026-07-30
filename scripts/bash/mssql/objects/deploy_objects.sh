#!/bin/bash
set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo "====================================="
echo "MSSQL OBJECTS DEPLOYMENT"
echo "====================================="

echo "----------------------------------------"
echo "Generating Database Objects : mssql"
echo "----------------------------------------"

python3 scripts/python/common/objects/bootstrap_generator.py mssql

echo "----------------------------------------"
echo "Deploying Database Objects : mssql"
echo "----------------------------------------"

python3 scripts/python/common/objects/deploy_objects.py mssql

echo "====================================="
echo "MSSQL OBJECTS DEPLOYMENT SUCCESSFUL"
echo "====================================="