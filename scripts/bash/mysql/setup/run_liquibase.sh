#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "RUNNING LIQUIBASE"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mysql.conf"

MYSQL_HOST=$(grep "^MYSQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_PORT=$(grep "^MYSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_DB=$(grep "^MYSQL_DB=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_USER=$(grep "^MYSQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_PASSWORD=$(grep "^MYSQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_DRIVER_VERSION=$(grep "^MYSQL_DRIVER_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

LB="$PROJECT_ROOT/tools/liquibase/liquibase"
DRIVER="$PROJECT_ROOT/tools/drivers/mysql-connector-j-${MYSQL_DRIVER_VERSION}.jar"
CHANGELOG="${1:-liquibase/mysql/master.xml}"

cd "$PROJECT_ROOT"

echo "Database : $MYSQL_DB"
echo "Host     : $MYSQL_HOST"
echo "Port     : $MYSQL_PORT"
echo "User     : $MYSQL_USER"
echo "Driver   : $DRIVER"
echo

java -version

echo

"$LB" \
--classpath="$DRIVER" \
--driver=com.mysql.cj.jdbc.Driver \
--changeLogFile="$CHANGELOG" \
--url="jdbc:mysql://$MYSQL_HOST:$MYSQL_PORT/$MYSQL_DB" \
--username="$MYSQL_USER" \
--password="$MYSQL_PASSWORD" \
update

echo
echo "====================================="
echo "LIQUIBASE UPDATE COMPLETED"
echo "====================================="
echo

exit 0
