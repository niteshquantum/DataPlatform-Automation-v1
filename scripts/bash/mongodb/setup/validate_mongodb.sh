#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

MONGODB_PORT=$(grep "^MONGODB_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

MONGOSH="$PROJECT_ROOT/databases/mongodb/mongosh/bin/mongosh"

echo
echo "====================================="
echo "VALIDATING MONGODB"
echo "====================================="
echo

"$MONGOSH" \
    --port "$MONGODB_PORT" \
    --eval "db.adminCommand({ ping: 1 })"

echo
echo "====================================="
echo "MONGODB VALIDATION SUCCESSFUL"
echo "====================================="
echo

exit 0