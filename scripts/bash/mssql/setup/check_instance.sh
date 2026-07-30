#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mssql.conf"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Configuration file not found: $CONFIG_FILE"
    echo "INSTANCE_STATE=NO_INSTANCE"
    exit 1
fi

MSSQL_PORT=$(grep "^MSSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "CHECKING MSSQL INSTANCE STATE"
echo "====================================="
echo

if [ ! -x "/opt/mssql/bin/sqlservr" ]; then
    echo "MSSQL is not installed."
    echo
    echo "INSTANCE_STATE=NO_INSTANCE"
    exit 1
fi

if systemctl is-active --quiet mssql-server; then
    if sudo ss -tlnp | grep sqlservr | grep -q ":${MSSQL_PORT}"; then
        echo "MSSQL is running and port ${MSSQL_PORT} is listening."
        echo
        echo "INSTANCE_STATE=INSTANCE_RUNNING_AND_USABLE"
        exit 0
    else
        echo "MSSQL is running but port ${MSSQL_PORT} is not listening."
        echo
        echo "INSTANCE_STATE=INSTANCE_INSTALLED_BUT_STOPPED"
        exit 1
    fi
else
    echo "MSSQL is installed but not running."
    echo
    echo "INSTANCE_STATE=INSTANCE_INSTALLED_BUT_STOPPED"
    exit 1
fi
