#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mysql.conf"

echo "SCRIPT_DIR   : $SCRIPT_DIR"
echo "PROJECT_ROOT : $PROJECT_ROOT"
echo "CONFIG_FILE  : $CONFIG_FILE"

echo
echo "====================================="
echo "CONFIGURING MYSQL USER"
echo "====================================="
echo

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found."
    exit 1
fi

# Load configuration
source "$CONFIG_FILE"

if [ -z "$MYSQL_USER" ] || [ -z "$MYSQL_PASSWORD" ]; then
    echo "ERROR: MYSQL_USER or MYSQL_PASSWORD is missing in config."
    exit 1
fi

echo "Configured User : $MYSQL_USER"

echo
echo "Checking whether user exists..."
USER_EXISTS=$(sudo /usr/bin/mysql -N -B -e "
SELECT COUNT(*)
FROM mysql.user
WHERE user='${MYSQL_USER}';
")
if [ "$USER_EXISTS" -gt 0 ]; then

    echo "User '$MYSQL_USER' already exists."
    echo "Skipping user creation."

else

    echo "Creating user '$MYSQL_USER'..."

    sudo /usr/bin/mysql <<EOF
CREATE USER '${MYSQL_USER}'@'localhost'
IDENTIFIED BY '${MYSQL_PASSWORD}';

GRANT ALL PRIVILEGES
ON *.*
TO '${MYSQL_USER}'@'localhost'
WITH GRANT OPTION;

FLUSH PRIVILEGES;
EOF

    echo "User created successfully."

fi

echo
echo "====================================="
echo "MYSQL USER CONFIGURED SUCCESSFULLY"
echo "====================================="