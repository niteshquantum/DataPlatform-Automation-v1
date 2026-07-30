#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

MONGODB_PORT=$(grep "^MONGODB_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "STOPPING MONGODB"
echo "====================================="
echo

PID=$(ss -tulnp 2>/dev/null | grep ":$MONGODB_PORT" | grep mongod | sed -E 's/.*pid=([0-9]+).*/\1/' | head -n1)

if [ -n "$PID" ]
then
    kill "$PID"

    echo "MongoDB process stopped (PID=$PID)"
else
    echo "MongoDB is not running"
fi

echo
echo "====================================="
echo "MONGODB STOPPED"
echo "====================================="
echo

exit 0