#!/bin/bash


set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

LOAD_MODE="${LOAD_MODE:-skip}"
export LOAD_MODE

echo
echo "====================================="
echo "MONGODB DATA LOAD"
echo "====================================="
echo

echo
echo "-------------------------------------"
echo "DETECTING SCHEMA"
echo "-------------------------------------"
echo

python3 scripts/schema_detector.py mongodb

echo
echo "-------------------------------------"
echo "LOADING DATA"
echo "-------------------------------------"
echo

echo "LOAD MODE : $LOAD_MODE"

python3 scripts/data_loader_mongodb.py

echo
echo "-------------------------------------"
echo "VALIDATING DATA"
echo "-------------------------------------"
echo

python3 scripts/python/mongodb/load/validate_data.py

echo
echo "====================================="
echo "DATA LOAD SUCCESSFUL"
echo "====================================="
echo

exit 0
