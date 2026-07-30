#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "CONFIGURING MSSQL SERVER"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mssql.conf"

# =====================================
# VALIDATE CONFIG
# =====================================

if [ ! -f "$CONFIG_FILE" ]
then
    echo "Configuration file not found."
    echo "Expected: $CONFIG_FILE"
    exit 1
fi

MSSQL_HOST=$(grep "^MSSQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PORT=$(grep "^MSSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_USER=$(grep "^MSSQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PASSWORD=$(grep "^MSSQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)

# =====================================
# VALIDATE INSTALLATION
# =====================================

if [ ! -x "/opt/mssql/bin/sqlservr" ]
then
    echo "SQL Server is not installed."
    exit 1
fi

if [ ! -x "/opt/mssql/bin/mssql-conf" ]
then
    echo "mssql-conf utility not found."
    exit 1
fi

SQLCMD="/opt/mssql-tools18/bin/sqlcmd"

if [ ! -x "$SQLCMD" ]
then
    echo "sqlcmd not found."
    exit 1
fi

# =====================================
# ENABLE SERVICE
# =====================================

echo "Enabling SQL Server service..."

sudo systemctl enable mssql-server

echo

# =====================================
# START / RESTART SERVICE
# =====================================

# =====================================
# START SERVICE IF REQUIRED
# =====================================

if sudo systemctl is-active --quiet mssql-server
then
    echo "SQL Server service is already running."
else
    echo "Starting SQL Server service..."
    sudo systemctl start mssql-server
fi

echo
echo "Waiting up to 120 seconds for SQL Server..."

# =====================================
# WAIT FOR SERVICE
# =====================================

for i in {1..60}
do
    if sudo systemctl is-active --quiet mssql-server
    then
        break
    fi

    sleep 2
done

# =====================================
# VALIDATE SERVICE
# =====================================

if ! sudo systemctl is-active --quiet mssql-server
then
    echo "SQL Server service failed to start."
    exit 1
fi

echo
echo "SQL Server service is running."

echo
echo "====================================="
echo "VALIDATING SQL SERVER CONNECTION"
echo "====================================="
echo

"$SQLCMD" \
-S "${MSSQL_HOST},${MSSQL_PORT}" \
-U "$MSSQL_USER" \
-P "$MSSQL_PASSWORD" \
-C \
-Q "SELECT @@VERSION;"

echo
echo "SQL Server connection validated."

echo "Host : $MSSQL_HOST"
echo "Port : $MSSQL_PORT"
echo "User : $MSSQL_USER"

echo
echo "====================================="
echo "MSSQL CONFIGURATION COMPLETED"
echo "====================================="
echo

exit 0
