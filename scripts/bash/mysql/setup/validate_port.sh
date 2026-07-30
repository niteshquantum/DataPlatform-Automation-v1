#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mysql.conf"

MYSQL_PORT=$(grep "^MYSQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "VALIDATING MYSQL PORT"
echo "====================================="
echo

if ss -ltn | grep -q ":${MYSQL_PORT}\b"
then
    echo "Port $MYSQL_PORT is LISTENING"
else
    echo "Port $MYSQL_PORT is NOT LISTENING"
    exit 1
fi

echo
echo "PORT VALIDATION SUCCESSFUL"
echo

exit 0