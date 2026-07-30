#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mssql.conf"

echo
echo "====================================="
echo "CONFIGURING GLOBAL MSSQL COMMAND"
echo "====================================="
echo

if [ ! -f "$CONFIG_FILE" ]
then
    echo "ERROR: MSSQL config file not found"
    echo "Expected: $CONFIG_FILE"
    exit 1
fi

MSSQL_HOST=$(grep "^MSSQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PORT=$(grep "^MSSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_DB=$(grep "^MSSQL_DB=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_USER=$(grep "^MSSQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PASSWORD=$(grep "^MSSQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)

REAL_SQLCMD="/opt/mssql-tools18/bin/sqlcmd"
GLOBAL_MSSQL="/usr/local/bin/mssql"

if [ ! -x "$REAL_SQLCMD" ]
then
    echo "ERROR: sqlcmd binary not found"
    echo "Expected: $REAL_SQLCMD"
    exit 1
fi

echo "Host     : $MSSQL_HOST"
echo "Port     : $MSSQL_PORT"
echo "Database : $MSSQL_DB"
echo "User     : $MSSQL_USER"

echo
echo "Creating global mssql wrapper..."

sudo rm -f "$GLOBAL_MSSQL"

sudo tee "$GLOBAL_MSSQL" > /dev/null <<EOF
#!/bin/bash

exec "$REAL_SQLCMD" \
-S "${MSSQL_HOST},${MSSQL_PORT}" \
-U "$MSSQL_USER" \
-P "$MSSQL_PASSWORD" \
-C \
"\$@"
EOF

sudo chmod +x "$GLOBAL_MSSQL"

echo
echo "Validating global mssql command..."

"$GLOBAL_MSSQL" -Q "SELECT @@VERSION;" > /dev/null

echo
echo "====================================="
echo "GLOBAL MSSQL CONFIGURED SUCCESSFULLY"
echo "====================================="
echo

echo "Command:"
echo "mssql"

exit 0
