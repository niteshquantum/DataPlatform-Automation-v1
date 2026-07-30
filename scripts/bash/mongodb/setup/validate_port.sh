#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

MONGODB_PORT=$(grep "^MONGODB_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "VALIDATING MONGODB PORT"
echo "====================================="
echo

if ss -ltn | grep ":$MONGODB_PORT " >/dev/null
then
    echo "Port $MONGODB_PORT is LISTENING"
else
    echo "Port $MONGODB_PORT is NOT LISTENING"
    exit 1
fi

echo
echo "PORT VALIDATION SUCCESSFUL"
echo

exit 0
