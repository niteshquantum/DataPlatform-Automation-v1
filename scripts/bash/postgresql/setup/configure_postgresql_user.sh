#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/postgresql.conf"

echo "SCRIPT_DIR   : $SCRIPT_DIR"
echo "PROJECT_ROOT : $PROJECT_ROOT"
echo "CONFIG_FILE  : $CONFIG_FILE"

echo
echo "====================================="
echo "CONFIGURING POSTGRESQL USER"
echo "====================================="
echo

if [ ! -f "$CONFIG_FILE" ]; then
    echo "ERROR: Config file not found."
    exit 1
fi

source "$CONFIG_FILE"

if [ -z "$POSTGRESQL_USER" ] || [ -z "$POSTGRESQL_PASSWORD" ]; then
    echo "ERROR: POSTGRESQL_USER or POSTGRESQL_PASSWORD is missing in config."
    exit 1
fi

echo "Configured User : $POSTGRESQL_USER"

echo
echo "Checking whether user exists..."

USER_EXISTS=$(sudo -u postgres psql -t -A -c "SELECT COUNT(*) FROM pg_roles WHERE rolname='${POSTGRESQL_USER}';" postgres)

if [ "$USER_EXISTS" -gt 0 ]; then

    echo "User '$POSTGRESQL_USER' already exists."
    echo "Skipping user creation."

else

    echo "Creating user '$POSTGRESQL_USER'..."

    sudo -u postgres psql -c "CREATE USER \"${POSTGRESQL_USER}\" WITH PASSWORD '${POSTGRESQL_PASSWORD}';" postgres

    sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${POSTGRESQL_DB}';" postgres | grep -q 1 || sudo -u postgres psql -c "CREATE DATABASE ${POSTGRESQL_DB};" postgres

    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${POSTGRESQL_DB} TO \"${POSTGRESQL_USER}\";" postgres

    echo "User created successfully."

fi

echo
echo "====================================="
echo "POSTGRESQL USER CONFIGURED SUCCESSFULLY"
echo "====================================="