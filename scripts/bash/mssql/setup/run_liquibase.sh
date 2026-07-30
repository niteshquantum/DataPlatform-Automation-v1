#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "RUNNING LIQUIBASE"
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
MSSQL_DRIVER_VERSION=$(grep "^MSSQL_DRIVER_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

LB="$PROJECT_ROOT/tools/liquibase/liquibase"

DRIVER="$PROJECT_ROOT/tools/drivers/mssql-jdbc-${MSSQL_DRIVER_VERSION}.jre11.jar"

CHANGELOG="${1:-liquibase/mssql/master.xml}"

if [ ! -f "$LB" ]
then
    echo "Liquibase executable not found."
    echo "$LB"
    exit 1
fi

if [ ! -f "$DRIVER" ]
then
    echo "MSSQL JDBC Driver not found."
    echo "$DRIVER"
    exit 1
fi

cd "$PROJECT_ROOT"

echo "Database : $MSSQL_DB"
echo "Host     : $MSSQL_HOST"
echo "Port     : $MSSQL_PORT"
echo "User     : $MSSQL_USER"
echo "Driver   : $DRIVER"
echo

java -version

echo

PASSWORD_OPTION=()

if [ -n "$MSSQL_PASSWORD" ]
then
    PASSWORD_OPTION=(--password="$MSSQL_PASSWORD")
fi

"$LB" \
--classpath="$DRIVER" \
--driver=com.microsoft.sqlserver.jdbc.SQLServerDriver \
--search-path="$PROJECT_ROOT" \
--changeLogFile="$CHANGELOG" \
--url="jdbc:sqlserver://$MSSQL_HOST:$MSSQL_PORT;databaseName=$MSSQL_DB;encrypt=true;trustServerCertificate=true" \
--username="$MSSQL_USER" \
"${PASSWORD_OPTION[@]}" \
update

echo
echo "====================================="
echo "LIQUIBASE UPDATE COMPLETED"
echo "====================================="
echo

exit 0
