#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

MONGODB_PORT=$(grep "^MONGODB_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

MONGODB_HOME="$PROJECT_ROOT/databases/mongodb/server"

DATA_DIR="$PROJECT_ROOT/databases/mongodb/data"

LOG_DIR="$PROJECT_ROOT/databases/mongodb/logs"

LOG_FILE="$LOG_DIR/mongod.log"

echo
echo "====================================="
echo "STARTING MONGODB"
echo "====================================="
echo

if ss -tulnp | grep -q ":$MONGODB_PORT"
then
    echo "MongoDB already running on port $MONGODB_PORT"

    echo
    echo "====================================="
    echo "MONGODB STARTED SUCCESSFULLY"
    echo "====================================="
    echo

    exit 0
fi

mkdir -p "$DATA_DIR"
mkdir -p "$LOG_DIR"

"$MONGODB_HOME/bin/mongod" \
    --dbpath "$DATA_DIR" \
    --logpath "$LOG_FILE" \
    --fork \
    --port "$MONGODB_PORT"

sleep 5

echo
echo "====================================="
echo "MONGODB STARTED SUCCESSFULLY"
echo "====================================="
echo

exit 0