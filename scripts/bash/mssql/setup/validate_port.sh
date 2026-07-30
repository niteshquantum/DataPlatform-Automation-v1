#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mssql.conf"

MSSQL_PORT=$(grep "^MSSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "VALIDATING MSSQL PORT"
echo "====================================="
echo

if sudo ss -tlnp | grep sqlservr | grep -q ":${MSSQL_PORT}"
then
    echo "Port $MSSQL_PORT is LISTENING"
else
    echo "Port $MSSQL_PORT is NOT LISTENING"
    exit 1
fi

echo
echo "PORT VALIDATION SUCCESSFUL"
echo

exit 0