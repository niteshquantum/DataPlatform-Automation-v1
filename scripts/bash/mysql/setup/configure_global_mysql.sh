
#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mysql.conf"

MYSQL_HOST=$(grep "^MYSQL_HOST=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_PORT=$(grep "^MYSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_DB=$(grep "^MYSQL_DB=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_USER=$(grep "^MYSQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
MYSQL_PASSWORD=$(grep "^MYSQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)

REAL_MYSQL="/usr/bin/mysql"
GLOBAL_MYSQL="/usr/local/bin/mysql"

echo
echo "====================================="
echo "CONFIGURING GLOBAL MYSQL COMMAND"
echo "====================================="
echo

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: MySQL config file not found"
    echo "Expected: $CONFIG_FILE"
    exit 1
fi

if [ ! -x "$REAL_MYSQL" ]; then
    echo "ERROR: MySQL client binary not found"
    echo "Expected: $REAL_MYSQL"
    exit 1
fi

echo "Host     : $MYSQL_HOST"
echo "Port     : $MYSQL_PORT"
echo "Database : $MYSQL_DB"
echo "User     : $MYSQL_USER"

echo
echo "Creating global mysql wrapper..."

sudo rm -f "$GLOBAL_MYSQL"

sudo tee "$GLOBAL_MYSQL" > /dev/null <<EOF
#!/bin/bash

exec "$REAL_MYSQL" \
--host="$MYSQL_HOST" \
--port="$MYSQL_PORT" \
--user="$MYSQL_USER" \
--password="$MYSQL_PASSWORD" \
"$MYSQL_DB" \
"\$@"
EOF

sudo chmod +x "$GLOBAL_MYSQL"

echo
echo "Validating global mysql command..."

"$GLOBAL_MYSQL" --version

echo
echo "====================================="
echo "GLOBAL MYSQL CONFIGURED SUCCESSFULLY"
echo "====================================="
echo

echo "Command:"
echo "mysql"

exit 0
