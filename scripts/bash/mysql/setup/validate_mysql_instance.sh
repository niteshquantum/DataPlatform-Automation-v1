#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mysql.conf"

MYSQL_HOST=$(grep "^MYSQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_PORT=$(grep "^MYSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_USER=$(grep "^MYSQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_PASSWORD=$(grep "^MYSQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "VALIDATING MYSQL INSTANCE"
echo "====================================="
echo

echo "Host     : $MYSQL_HOST"
echo "Port     : $MYSQL_PORT"
echo "User     : $MYSQL_USER"
echo

echo "Testing MySQL connection..."

/usr/bin/mysql \
-h "$MYSQL_HOST" \
-P "$MYSQL_PORT" \
-u "$MYSQL_USER" \
-p"$MYSQL_PASSWORD" \
-e "SELECT VERSION() AS version, @@port AS actual_port, @@hostname AS hostname;"

echo
echo "MYSQL INSTANCE VALIDATION SUCCESSFUL"
echo

exit 0
