#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

cd "$PROJECT_ROOT"

DB="$1"
if [ -z "$DB" ]; then
    echo "ERROR: Database type not provided"
    exit 1
fi

SCHEMA_REGISTRY="$PROJECT_ROOT/metadata/$DB/schema_registry.json"
DATATYPE_REGISTRY="$PROJECT_ROOT/metadata/$DB/datatype_registry.json"

echo
echo "====================================="
echo "VALIDATING METADATA"
echo "====================================="
echo

if [ ! -f "$SCHEMA_REGISTRY" ]; then
    echo "ERROR: schema_registry.json not found at $SCHEMA_REGISTRY"
    exit 1
fi

if [ ! -f "$DATATYPE_REGISTRY" ]; then
    echo "ERROR: datatype_registry.json not found at $DATATYPE_REGISTRY"
    exit 1
fi

python3 -c "import json; json.load(open('$SCHEMA_REGISTRY'))"
python3 -c "import json; json.load(open('$DATATYPE_REGISTRY'))"

echo "METADATA VALIDATION SUCCESSFUL"
echo

exit 0
