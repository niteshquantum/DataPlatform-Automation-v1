#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mssql.conf"

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Configuration file not found: $CONFIG_FILE"
    exit 1
fi

MSSQL_HOST=$(grep "^MSSQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PORT=$(grep "^MSSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_USER=$(grep "^MSSQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PASSWORD=$(grep "^MSSQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "VALIDATING MSSQL INSTANCE"
echo "====================================="
echo

echo "Host : $MSSQL_HOST"
echo "Port : $MSSQL_PORT"
echo "User : $MSSQL_USER"
echo

echo "Testing MSSQL instance connection..."

sqlcmd \
    -S "${MSSQL_HOST},${MSSQL_PORT}" \
    -U "${MSSQL_USER}" \
    -P "${MSSQL_PASSWORD}" \
    -C \
    -Q "SELECT @@VERSION AS version, CONNECTIONPROPERTY('local_net_address') AS local_address, CONNECTIONPROPERTY('local_tcp_port') AS local_port;"

echo
echo "MSSQL INSTANCE VALIDATION SUCCESSFUL"
echo

exit 0
