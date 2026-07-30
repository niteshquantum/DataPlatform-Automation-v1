#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "STOPPING POSTGRESQL SERVER"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/postgresql.conf"

# =====================================
# VALIDATE CONFIG
# =====================================

if [ ! -f "$CONFIG_FILE" ]
then
    echo "ERROR: PostgreSQL configuration file not found:"
    echo "$CONFIG_FILE"
    exit 1
fi

POSTGRESQL_VERSION=$(
    grep "^POSTGRESQL_VERSION=" "$CONFIG_FILE" |
    cut -d'=' -f2 |
    tr -d '\r' |
    xargs
)

if [ -z "$POSTGRESQL_VERSION" ]
then
    echo "ERROR: POSTGRESQL_VERSION is missing."
    exit 1
fi

echo "PostgreSQL Version : $POSTGRESQL_VERSION"
echo

# =====================================
# CHECK POSTGRESQL INSTALLATION
# =====================================

if [ ! -x "/usr/lib/postgresql/$POSTGRESQL_VERSION/bin/postgres" ]
then
    echo "PostgreSQL $POSTGRESQL_VERSION is not installed."
    echo "Nothing to stop."
    echo

    exit 0
fi

# =====================================
# CHECK POSTGRESQL SERVICE
# =====================================

if ! systemctl list-unit-files postgresql.service \
    >/dev/null 2>&1
then
    echo "PostgreSQL service does not exist."
    echo "Nothing to stop."
    echo

    exit 0
fi

# =====================================
# STOP POSTGRESQL
# =====================================

if systemctl is-active --quiet postgresql
then

    echo "PostgreSQL service is running."
    echo "Stopping PostgreSQL service..."
    echo

    sudo systemctl stop postgresql

else

    echo "PostgreSQL service is already stopped."

fi

# =====================================
# VALIDATE SERVICE STATUS
# =====================================

echo
echo "Validating PostgreSQL service status..."
echo

if systemctl is-active --quiet postgresql
then
    echo "ERROR: PostgreSQL service is still running."
    exit 1
fi

echo "PostgreSQL service validation passed."

echo
echo "====================================="
echo "POSTGRESQL STOP SUCCESSFUL"
echo "====================================="
echo

exit 0