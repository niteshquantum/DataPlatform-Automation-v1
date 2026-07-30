#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING MSSQL SERVER"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mssql.conf"

if [ ! -f "$CONFIG_FILE" ]
then
    echo "Configuration file not found:"
    echo "$CONFIG_FILE"
    exit 1
fi

MSSQL_HOST=$(grep "^MSSQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PORT=$(grep "^MSSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_DB=$(grep "^MSSQL_DB=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_USER=$(grep "^MSSQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PASSWORD=$(grep "^MSSQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)

SQLCMD="/opt/mssql-tools18/bin/sqlcmd"

if [ ! -x "$SQLCMD" ]
then
    echo "sqlcmd is not installed."
    exit 1
fi

if [ ! -x "/opt/mssql/bin/sqlservr" ]
then
    echo "SQL Server is not installed."
    exit 1
fi

echo "Checking SQL Server service..."

if ! systemctl is-active --quiet mssql-server
then
    echo "SQL Server service is not running."
    exit 1
fi

echo "Checking SQL Server port..."

if ! sudo ss -tlnp | grep sqlservr | grep -q ":${MSSQL_PORT}"
then
    echo "SQL Server is not listening on port ${MSSQL_PORT}."
    exit 1
fi

echo "Validating SQL Server connection..."

"$SQLCMD" \
-S "${MSSQL_HOST},${MSSQL_PORT}" \
-U "${MSSQL_USER}" \
-P "${MSSQL_PASSWORD}" \
-C \
-l 30 \
-Q "SELECT @@VERSION;" > /dev/null


echo
echo "====================================="
echo "MSSQL SERVER VALIDATION SUCCESSFUL"
echo "====================================="
echo

exit 0