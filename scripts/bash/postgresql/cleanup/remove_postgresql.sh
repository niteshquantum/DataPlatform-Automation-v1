#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "REMOVING POSTGRESQL DEPLOYMENT"
echo "====================================="
echo

# =====================================
# CONFIGURATION
# =====================================

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/postgresql.conf"

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

# =====================================
# CLEANUP MODE
# =====================================

CLEANUP_MODE="${CLEANUP_MODE:-PRESERVE_DATA}"
CLEANUP_MODE="$(echo "$CLEANUP_MODE" | tr '[:lower:]' '[:upper:]')"

if [[ "$CLEANUP_MODE" != "PRESERVE_DATA" && \
      "$CLEANUP_MODE" != "DELETE_DATA" ]]
then
    echo "ERROR: Invalid CLEANUP_MODE: $CLEANUP_MODE"
    exit 1
fi

echo "Project Root       : $PROJECT_ROOT"
echo "PostgreSQL Version : $POSTGRESQL_VERSION"
echo "Cleanup Mode       : $CLEANUP_MODE"
echo

# =====================================
# PRESERVE DATA MODE
# =====================================

if [ "$CLEANUP_MODE" = "PRESERVE_DATA" ]
then

    echo "Applying PRESERVE_DATA cleanup..."
    echo
    echo "PostgreSQL installation will be preserved."
    echo "PostgreSQL database data will be preserved."
    echo

    echo "====================================="
    echo "POSTGRESQL DEPLOYMENT PRESERVED"
    echo "====================================="
    echo

    exit 0
fi

# =====================================
# DELETE DATA MODE
# =====================================

echo "Applying DELETE_DATA cleanup..."
echo

# =====================================
# CHECK INSTALLATION
# =====================================

if ! dpkg-query -W -f='${Status}' \
    "postgresql-$POSTGRESQL_VERSION" \
    2>/dev/null | grep -q "install ok installed"
then

    echo "PostgreSQL $POSTGRESQL_VERSION package is not installed."
    echo "Nothing to remove."
    echo

    exit 0
fi

# =====================================
# PURGE POSTGRESQL PACKAGES
# =====================================

echo "Removing PostgreSQL packages..."
echo

sudo DEBIAN_FRONTEND=noninteractive \
    apt-get purge -y \
    "postgresql-$POSTGRESQL_VERSION" \
    "postgresql-client-$POSTGRESQL_VERSION"

echo
echo "PostgreSQL packages removed successfully."
echo

# =====================================
# REMOVE UNUSED DEPENDENCIES
# =====================================

echo "Removing unused PostgreSQL dependencies..."
echo

sudo DEBIAN_FRONTEND=noninteractive \
    apt-get autoremove -y

echo
echo "Unused dependencies cleanup completed."
echo

# =====================================
# REMOVE VERSION DATA
# =====================================

POSTGRESQL_DATA_DIR="/var/lib/postgresql/$POSTGRESQL_VERSION"

echo "Removing PostgreSQL data directory..."
echo "Path : $POSTGRESQL_DATA_DIR"
echo

if [ -d "$POSTGRESQL_DATA_DIR" ]
then

    sudo rm -rf "$POSTGRESQL_DATA_DIR"

    echo "PostgreSQL data directory removed successfully."

else

    echo "PostgreSQL data directory already absent."

fi

# =====================================
# REMOVE VERSION CONFIGURATION
# =====================================

POSTGRESQL_CONFIG_DIR="/etc/postgresql/$POSTGRESQL_VERSION"

echo
echo "Removing PostgreSQL configuration directory..."
echo "Path : $POSTGRESQL_CONFIG_DIR"
echo

if [ -d "$POSTGRESQL_CONFIG_DIR" ]
then

    sudo rm -rf "$POSTGRESQL_CONFIG_DIR"

    echo "PostgreSQL configuration directory removed successfully."

else

    echo "PostgreSQL configuration directory already absent."

fi

# =====================================
# VALIDATE REMOVAL
# =====================================

echo
echo "Validating PostgreSQL removal..."
echo

if dpkg-query -W -f='${Status}' \
    "postgresql-$POSTGRESQL_VERSION" \
    2>/dev/null | grep -q "install ok installed"
then
    echo "ERROR: PostgreSQL package still exists."
    exit 1
fi

if [ -d "$POSTGRESQL_DATA_DIR" ]
then
    echo "ERROR: PostgreSQL data directory still exists."
    exit 1
fi

if [ -d "$POSTGRESQL_CONFIG_DIR" ]
then
    echo "ERROR: PostgreSQL configuration directory still exists."
    exit 1
fi

echo "PostgreSQL removal validation passed."

echo
echo "====================================="
echo "POSTGRESQL DEPLOYMENT REMOVAL COMPLETE"
echo "====================================="
echo
echo "Cleanup Mode : $CLEANUP_MODE"
echo

exit 0