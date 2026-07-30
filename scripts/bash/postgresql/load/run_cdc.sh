#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo
echo "-------------------------------------"
echo "CDC CHECK"
echo "-------------------------------------"
echo

SCHEMA_STATUS="$PROJECT_ROOT/metadata/postgresql/schema_status.json"

if [ ! -f "$SCHEMA_STATUS" ]; then
    echo "SCHEMA STATUS FILE NOT FOUND: $SCHEMA_STATUS"
    echo "Assuming schema changed, proceeding with full load."
    exit 0
fi

SCHEMA_CHANGED=$(python3 -c "import json; f=open('$SCHEMA_STATUS','r'); d=json.load(f); f.close(); print(str(d.get('schema_changed',False)).lower())")

if [ "$SCHEMA_CHANGED" = "true" ]; then
    echo "Schema changes detected. Proceeding with full load."
    exit 0
fi

echo "No schema changes detected. Running CDC..."
python3 scripts/cdc/cdc_engine.py postgresql
CDC_EXIT=$?

if [ $CDC_EXIT -eq 0 ]; then
    echo "File changes detected. Proceeding with full load."
    exit 0
fi

if [ $CDC_EXIT -eq 100 ]; then
    echo "No file changes detected. Skipping data load."
    exit 100
fi

echo "CDC execution failed with exit code $CDC_EXIT."
exit $CDC_EXIT
