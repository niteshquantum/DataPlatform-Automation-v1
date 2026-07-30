#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mssql.conf"

echo "SCRIPT_DIR   : $SCRIPT_DIR"
echo "PROJECT_ROOT : $PROJECT_ROOT"
echo "CONFIG_FILE  : $CONFIG_FILE"

echo
echo "====================================="
echo "CONFIGURING MSSQL USER"
echo "====================================="
echo

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found."
    exit 1
fi

source "$CONFIG_FILE"

if [ -z "$MSSQL_USER" ] || [ -z "$MSSQL_PASSWORD" ]; then
    echo "ERROR: MSSQL_USER or MSSQL_PASSWORD is missing in config."
    exit 1
fi

echo "Configured User : $MSSQL_USER"

SQLCMD="/opt/mssql-tools18/bin/sqlcmd"

if [ ! -x "$SQLCMD" ]; then
    echo "ERROR: sqlcmd not found."
    exit 1
fi

echo
echo "Checking whether login exists..."

LOGIN_EXISTS=$($SQLCMD \
    -S "${MSSQL_HOST},${MSSQL_PORT}" \
    -U sa \
    -P "$MSSQL_PASSWORD" \
    -C \
    -Q "SET NOCOUNT ON; SELECT COUNT(*) FROM sys.server_principals WHERE name='${MSSQL_USER}';" \
    -h -1 -W 2>/dev/null | tr -d '[:space:]')

if [ "$LOGIN_EXISTS" -gt 0 ]; then

    echo "Login '$MSSQL_USER' already exists."
    echo "Skipping login creation."

else

    echo "Creating login '$MSSQL_USER'..."

    $SQLCMD \
        -S "${MSSQL_HOST},${MSSQL_PORT}" \
        -U sa \
        -P "$MSSQL_PASSWORD" \
        -C \
        -Q "CREATE LOGIN [${MSSQL_USER}] WITH PASSWORD = '${MSSQL_PASSWORD}';" \
        -b

    $SQLCMD \
        -S "${MSSQL_HOST},${MSSQL_PORT}" \
        -U sa \
        -P "$MSSQL_PASSWORD" \
        -C \
        -Q "ALTER SERVER ROLE sysadmin ADD MEMBER [${MSSQL_USER}];" \
        -b

    echo "Login created successfully."

fi

echo
echo "====================================="
echo "MSSQL USER CONFIGURED SUCCESSFULLY"
echo "====================================="