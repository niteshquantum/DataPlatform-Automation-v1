#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING POSTGRESQL CLEANUP"
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
# PATHS
# =====================================

POSTGRESQL_DATA_DIR="/var/lib/postgresql/$POSTGRESQL_VERSION"
POSTGRESQL_CONFIG_DIR="/etc/postgresql/$POSTGRESQL_VERSION"

LIQUIBASE_DIR="$PROJECT_ROOT/liquibase/postgresql"
MASTER_XML="$LIQUIBASE_DIR/master.xml"

HISTORY_FILE="$PROJECT_ROOT/metadata/postgresql/data_load_history.jsonl"
ARCHIVE_DIR="$PROJECT_ROOT/archive/postgresql"
FAILED_DIR="$PROJECT_ROOT/failed/postgresql"
INCOMING_DIR="$PROJECT_ROOT/incoming/postgresql"

# =====================================
# VALIDATE POSTGRESQL
# =====================================

echo "Checking PostgreSQL installation and service..."
echo

if [ "$CLEANUP_MODE" = "PRESERVE_DATA" ]
then

    if [ ! -x "/usr/lib/postgresql/$POSTGRESQL_VERSION/bin/postgres" ]
    then
        echo "ERROR: PostgreSQL installation should remain in PRESERVE_DATA mode."
        exit 1
    fi

    if systemctl is-active --quiet postgresql
    then
        echo "ERROR: PostgreSQL service should be stopped after cleanup."
        exit 1
    fi

    echo "PostgreSQL installation preservation validated successfully."
    echo "PostgreSQL service is stopped successfully."

else

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

    echo "PostgreSQL installation removal validated successfully."
    echo "PostgreSQL data removal validated successfully."
    echo "PostgreSQL configuration removal validated successfully."

fi

# =====================================
# VALIDATE LIQUIBASE XML
# =====================================

echo
echo "Checking PostgreSQL Liquibase XML state..."
echo

if [ "$CLEANUP_MODE" = "DELETE_DATA" ]
then

    REMAINING_XML="$(
        find "$LIQUIBASE_DIR" \
            -maxdepth 1 \
            -type f \
            -name "*.xml" \
            ! -name "master.xml" \
            -print -quit 2>/dev/null
    )"

    if [ -n "$REMAINING_XML" ]
    then
        echo "ERROR: Generated PostgreSQL Liquibase XML files still exist."
        exit 1
    fi

    if [ ! -f "$MASTER_XML" ]
    then
        echo "ERROR: PostgreSQL master.xml does not exist."
        exit 1
    fi

    echo "PostgreSQL Liquibase XML cleanup validated successfully."

else

    echo "PostgreSQL Liquibase XML preserved in PRESERVE_DATA mode."

fi

# =====================================
# VALIDATE LOAD ARTIFACTS
# =====================================

echo
echo "Checking PostgreSQL load artifacts..."
echo

if [ "$CLEANUP_MODE" = "DELETE_DATA" ]
then

    if [ -f "$HISTORY_FILE" ]
    then
        echo "ERROR: PostgreSQL data load history still exists."
        exit 1
    fi

    if [ -d "$ARCHIVE_DIR" ] && \
       [ -n "$(find "$ARCHIVE_DIR" -mindepth 1 -print -quit)" ]
    then
        echo "ERROR: PostgreSQL archive artifacts still exist."
        exit 1
    fi

    if [ -d "$FAILED_DIR" ] && \
       [ -n "$(find "$FAILED_DIR" -mindepth 1 -print -quit)" ]
    then
        echo "ERROR: PostgreSQL failed artifacts still exist."
        exit 1
    fi

    echo "PostgreSQL load artifacts cleanup validated successfully."

else

    echo "PostgreSQL load artifacts preserved in PRESERVE_DATA mode."

fi

# =====================================
# VALIDATE INCOMING DIRECTORY
# =====================================

echo
echo "Checking incoming source directory..."
echo

if [ -d "$INCOMING_DIR" ]
then
    echo "PostgreSQL incoming source directory preserved."
else
    echo "PostgreSQL incoming source directory does not currently exist."
    echo "No cleanup validation failure required."
fi

# =====================================
# SUCCESS
# =====================================

echo
echo "====================================="
echo "POSTGRESQL CLEANUP VALIDATION SUCCESSFUL"
echo "====================================="
echo
echo "Cleanup Mode : $CLEANUP_MODE"
echo

exit 0