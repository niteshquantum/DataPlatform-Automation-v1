#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

MONGODB_PORT=$(grep "^MONGODB_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
MONGODB_HOST=$(grep "^MONGODB_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)

MONGOSH="$PROJECT_ROOT/databases/mongodb/mongosh/bin/mongosh"

if [ ! -x "$MONGOSH" ]; then
    MONGOSH=$(command -v mongosh)
fi

if [ -z "$MONGOSH" ]; then
    echo "ERROR: mongosh command not found."
    exit 1
fi

echo
echo "====================================="
echo "VALIDATING MONGODB"
echo "====================================="
echo

"$MONGOSH" \
    --host "$MONGODB_HOST" \
    --port "$MONGODB_PORT" \
    --eval "db.adminCommand({ ping: 1 })"

echo
echo "====================================="
echo "MONGODB VALIDATION SUCCESSFUL"
echo "====================================="
echo

exit 0