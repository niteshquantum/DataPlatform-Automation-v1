#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

echo
echo "====================================="
echo "RUNNING LIQUIBASE"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mssql.conf"

MSSQL_HOST=$(grep "^MSSQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PORT=$(grep "^MSSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_DB=$(grep "^MSSQL_DB=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_USER=$(grep "^MSSQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_PASSWORD=$(grep "^MSSQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)
MSSQL_DRIVER_VERSION=$(grep "^MSSQL_DRIVER_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

LB="$PROJECT_ROOT/tools/liquibase/liquibase"

DRIVER="$PROJECT_ROOT/tools/drivers/mssql-jdbc-${MSSQL_DRIVER_VERSION}.jre11.jar"

CHANGELOG="liquibase/mssql/master.xml"

cd "$PROJECT_ROOT"

"$LB" \
--classpath="$DRIVER" \
--driver=com.microsoft.sqlserver.jdbc.SQLServerDriver \
--changeLogFile="$CHANGELOG" \
--url="jdbc:sqlserver://$MSSQL_HOST:$MSSQL_PORT;databaseName=$MSSQL_DB;encrypt=true;trustServerCertificate=true" \
--username="$MSSQL_USER" \
--password="$MSSQL_PASSWORD" \
update

echo
echo "====================================="
echo "LIQUIBASE UPDATE COMPLETED"
echo "====================================="
echo

exit 0