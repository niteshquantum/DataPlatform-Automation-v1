#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mssql.conf"

MSSQL_HOST=$(grep "^MSSQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PORT=$(grep "^MSSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_DB=$(grep "^MSSQL_DB=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_USER=$(grep "^MSSQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PASSWORD=$(grep "^MSSQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "VALIDATING ENVIRONMENT"
echo "====================================="
echo

sqlcmd \
-S ${MSSQL_HOST},${MSSQL_PORT} \
-U ${MSSQL_USER} \
-P "${MSSQL_PASSWORD}" \
-C \
-d ${MSSQL_DB} \
-Q "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES"

echo
echo "====================================="
echo "ENVIRONMENT VALIDATION SUCCESSFUL"
echo "====================================="
echo

exit 0