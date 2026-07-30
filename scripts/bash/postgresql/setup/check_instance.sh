#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/postgresql.conf"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Configuration file not found: $CONFIG_FILE"
    echo "INSTANCE_STATE=UNKNOWN"
    exit 1
fi

POSTGRESQL_PORT=$(grep "^POSTGRESQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
POSTGRESQL_VERSION=$(grep "^POSTGRESQL_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "CHECKING POSTGRESQL INSTANCE STATE"
echo "====================================="
echo

if [ ! -x "/usr/lib/postgresql/$POSTGRESQL_VERSION/bin/initdb" ]; then
    echo "PostgreSQL $POSTGRESQL_VERSION is not installed."
    echo
    echo "INSTANCE_STATE=NO_INSTANCE"
    exit 1
fi

if systemctl is-active --quiet postgresql; then
    if sudo ss -tlnp | grep postgres | grep -q ":${POSTGRESQL_PORT}"; then
        echo "PostgreSQL is running and port ${POSTGRESQL_PORT} is listening."
        echo
        echo "INSTANCE_STATE=INSTANCE_RUNNING_AND_USABLE"
        exit 0
    else
        echo "PostgreSQL is running but port ${POSTGRESQL_PORT} is not listening."
        echo
        echo "INSTANCE_STATE=INSTANCE_INSTALLED_BUT_STOPPED"
        exit 1
    fi
else
    echo "PostgreSQL is installed but not running."
    echo
    echo "INSTANCE_STATE=INSTANCE_INSTALLED_BUT_STOPPED"
    exit 1
fi
