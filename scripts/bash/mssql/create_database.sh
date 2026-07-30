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
echo "CREATING DATABASE"
echo "====================================="
echo

sqlcmd \
-S ${MSSQL_HOST},${MSSQL_PORT} \
-U ${MSSQL_USER} \
-P "${MSSQL_PASSWORD}" \
-C \
-Q "
IF DB_ID('${MSSQL_DB}') IS NULL
    CREATE DATABASE [${MSSQL_DB}]
"

echo "Database Checked : ${MSSQL_DB}"

echo
echo "====================================="
echo "DATABASE READY"
echo "====================================="
echo

exit 0