#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo
echo "====================================="
echo "MYSQL OBJECTS DEPLOYMENT"
echo "====================================="
echo

python3 scripts/python/common/objects/bootstrap_generator.py mysql

python3 scripts/python/common/objects/deploy_objects.py mysql

echo
echo "====================================="
echo "MYSQL OBJECTS DEPLOYMENT SUCCESSFUL"
echo "====================================="
echo

exit 0
