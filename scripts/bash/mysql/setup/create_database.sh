#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "CREATE DATABASE"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mysql.conf"

MYSQL_HOST=$(grep "^MYSQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_PORT=$(grep "^MYSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_DB=$(grep "^MYSQL_DB=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_USER=$(grep "^MYSQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_PASSWORD=$(grep "^MYSQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)

echo "Host     : $MYSQL_HOST"
echo "Port     : $MYSQL_PORT"
echo "Database : $MYSQL_DB"
echo "User     : $MYSQL_USER"
echo

echo "Configuring MySQL application user..."

sudo /usr/bin/mysql <<EOF
CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'localhost'
IDENTIFIED BY '${MYSQL_PASSWORD}';

ALTER USER '${MYSQL_USER}'@'localhost'
IDENTIFIED BY '${MYSQL_PASSWORD}';

CREATE USER IF NOT EXISTS '${MYSQL_USER}'@'127.0.0.1'
IDENTIFIED BY '${MYSQL_PASSWORD}';

ALTER USER '${MYSQL_USER}'@'127.0.0.1'
IDENTIFIED BY '${MYSQL_PASSWORD}';

GRANT ALL PRIVILEGES ON *.* TO '${MYSQL_USER}'@'localhost'
WITH GRANT OPTION;

GRANT ALL PRIVILEGES ON *.* TO '${MYSQL_USER}'@'127.0.0.1'
WITH GRANT OPTION;

FLUSH PRIVILEGES;
EOF

echo "MySQL application user configured successfully."

echo
echo "Creating database if not exists..."

MYSQL_PWD="$MYSQL_PASSWORD" /usr/bin/mysql \
-h "$MYSQL_HOST" \
-P "$MYSQL_PORT" \
-u "$MYSQL_USER" \
-e "CREATE DATABASE IF NOT EXISTS \`$MYSQL_DB\`;"

echo
echo "DATABASE READY : $MYSQL_DB"

echo
echo "====================================="
echo "DATABASE VALIDATED"
echo "====================================="
echo

exit 0
