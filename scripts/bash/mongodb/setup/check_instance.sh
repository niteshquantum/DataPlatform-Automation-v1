#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mongodb.conf"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Configuration file not found: $CONFIG_FILE"
    echo "INSTANCE_STATE=UNKNOWN"
    exit 1
fi

MONGODB_PORT=$(grep "^MONGODB_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "CHECKING MONGODB INSTANCE STATE"
echo "====================================="
echo

SERVICE_NAME="mongodb-automation"

if ! systemctl list-unit-files | grep -q "^${SERVICE_NAME}.service"; then
    echo "MongoDB service is not installed."
    echo
    echo "INSTANCE_STATE=NO_INSTANCE"
    exit 0
fi

if systemctl is-active --quiet "$SERVICE_NAME"; then

    if sudo ss -tlnp | grep -q ":${MONGODB_PORT}"; then
        echo "MongoDB is running and port ${MONGODB_PORT} is listening."
        echo
        echo "INSTANCE_STATE=INSTANCE_RUNNING_AND_USABLE"
        exit 0
    else
        echo "MongoDB service is running but port ${MONGODB_PORT} is not listening."
        echo
        echo "INSTANCE_STATE=INSTANCE_INSTALLED_BUT_STOPPED"
        exit 1
    fi

else

    echo "MongoDB is installed but not running."
    echo
    echo "INSTANCE_STATE=INSTANCE_INSTALLED_BUT_STOPPED"
    exit 1

fi