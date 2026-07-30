#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "RUNNING LIQUIBASE"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/postgresql.conf"

POSTGRESQL_HOST=$(grep "^POSTGRESQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
POSTGRESQL_PORT=$(grep "^POSTGRESQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
POSTGRESQL_DB=$(grep "^POSTGRESQL_DB=" "$CONFIG_FILE" | cut -d'=' -f2)
POSTGRESQL_USER=$(grep "^POSTGRESQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
POSTGRESQL_PASSWORD=$(grep "^POSTGRESQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)
POSTGRESQL_DRIVER_VERSION=$(grep "^POSTGRESQL_DRIVER_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

LB="$PROJECT_ROOT/tools/liquibase/liquibase"
DRIVER="$PROJECT_ROOT/tools/drivers/postgresql-${POSTGRESQL_DRIVER_VERSION}.jar"
CHANGELOG="${1:-liquibase/postgresql/master.xml}"

cd "$PROJECT_ROOT"

echo "Database : $POSTGRESQL_DB"
echo "Host     : $POSTGRESQL_HOST"
echo "Port     : $POSTGRESQL_PORT"
echo "User     : $POSTGRESQL_USER"
echo "Driver   : $DRIVER"
echo

java -version

echo

"$LB" \
--classpath="$DRIVER" \
--driver=org.postgresql.Driver \
--changeLogFile="$CHANGELOG" \
--url="jdbc:postgresql://$POSTGRESQL_HOST:$POSTGRESQL_PORT/$POSTGRESQL_DB" \
--username="$POSTGRESQL_USER" \
--password="$POSTGRESQL_PASSWORD" \
update

echo
echo "====================================="
echo "LIQUIBASE UPDATE COMPLETED"
echo "====================================="
echo

exit 0
