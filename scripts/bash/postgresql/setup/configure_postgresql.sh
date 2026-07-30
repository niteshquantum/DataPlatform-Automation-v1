#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/postgresql.conf"

USER=$(grep "^POSTGRESQL_USER=" "$CONFIG_FILE" | cut -d'=' -f2)
PASSWORD=$(grep "^POSTGRESQL_PASSWORD=" "$CONFIG_FILE" | cut -d'=' -f2)
PORT=$(grep "^POSTGRESQL_PORT=" "$CONFIG_FILE" | cut -d'=' -f2)

echo
echo "====================================="
echo "CONFIGURING POSTGRESQL USER"
echo "====================================="
echo

echo "Configuring user on port: $PORT"

sudo -u postgres psql \
    -p "$PORT" \
    -d postgres \
    -c "ALTER USER \"$USER\" WITH PASSWORD '$PASSWORD';"

echo
echo "POSTGRESQL USER CONFIGURED SUCCESSFULLY"
echo

exit 0
