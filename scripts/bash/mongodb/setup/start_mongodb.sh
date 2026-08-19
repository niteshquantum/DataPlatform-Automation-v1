#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

MONGODB_HOST=$(grep "^MONGODB_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MONGODB_PORT=$(grep "^MONGODB_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

MONGODB_HOME="$PROJECT_ROOT/databases/mongodb/server"
MONGOD_BINARY="$MONGODB_HOME/bin/mongod"

MONGOSH="$PROJECT_ROOT/databases/mongodb/mongosh/bin/mongosh"

DATA_DIR="$PROJECT_ROOT/databases/mongodb/data"
LOG_DIR="$PROJECT_ROOT/databases/mongodb/logs"
LOG_FILE="$LOG_DIR/mongod.log"

echo
echo "====================================="
echo "STARTING MONGODB"
echo "====================================="
echo

if [ ! -f "$MONGOD_BINARY" ]; then
    echo "ERROR: MongoDB binary not found."
    echo "Expected: $MONGOD_BINARY"
    exit 1
fi

if [ ! -f "$MONGOSH" ]; then
    echo "ERROR: mongosh binary not found."
    echo "Expected: $MONGOSH"
    exit 1
fi

if ss -tln | grep -q ":${MONGODB_PORT} "; then

    echo "Port ${MONGODB_PORT} is already in use."
    echo "Checking whether MongoDB is already running..."

    if "$MONGOSH" \
        --host "$MONGODB_HOST" \
        --port "$MONGODB_PORT" \
        --eval "db.adminCommand({ ping: 1 })" > /dev/null 2>&1; then

        echo "MongoDB is already running on port ${MONGODB_PORT}."

        echo
        echo "====================================="
        echo "MONGODB STARTED SUCCESSFULLY"
        echo "====================================="
        echo

        exit 0
    fi

    echo "ERROR: Port ${MONGODB_PORT} is already in use, but MongoDB is not responding."
    exit 1
fi

mkdir -p "$DATA_DIR"
mkdir -p "$LOG_DIR"

"$MONGOD_BINARY" \
    --dbpath "$DATA_DIR" \
    --logpath "$LOG_FILE" \
    --fork \
    --port "$MONGODB_PORT"

sleep 5

if ! "$MONGOSH" \
    --host "$MONGODB_HOST" \
    --port "$MONGODB_PORT" \
    --eval "db.adminCommand({ ping: 1 })" > /dev/null 2>&1; then

    echo "ERROR: MongoDB failed to start successfully."
    exit 1
fi

echo "MongoDB started successfully on port ${MONGODB_PORT}."

echo
echo "====================================="
echo "MONGODB STARTED SUCCESSFULLY"
echo "====================================="
echo

exit 0