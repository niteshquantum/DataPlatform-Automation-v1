#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mysql.conf"

MYSQL_HOST=$(grep "^MYSQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_PORT=$(grep "^MYSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_DB=$(grep "^MYSQL_DB=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_USER=$(grep "^MYSQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_PASSWORD=$(grep "^MYSQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "VALIDATING MYSQL"
echo "====================================="
echo

/usr/bin/mysql \
-h "$MYSQL_HOST" \
-P "$MYSQL_PORT" \
-u "$MYSQL_USER" \
-p"$MYSQL_PASSWORD" \
-e "USE $MYSQL_DB; SELECT DATABASE();"

echo
echo "MYSQL VALIDATION SUCCESSFUL"
echo

exit 0
