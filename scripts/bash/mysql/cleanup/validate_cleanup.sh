#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING MYSQL CLEANUP"
echo "====================================="
echo

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

echo "Project Root : $PROJECT_ROOT"
echo "Cleanup Mode : $CLEANUP_MODE"
echo

# =====================================
# PATHS
# =====================================

LIQUIBASE_DIR="$PROJECT_ROOT/liquibase/mysql"
MASTER_XML="$LIQUIBASE_DIR/master.xml"

HISTORY_FILE="$PROJECT_ROOT/metadata/mysql/data_load_history.jsonl"
ARCHIVE_DIR="$PROJECT_ROOT/archive/mysql"
FAILED_DIR="$PROJECT_ROOT/failed/mysql"
INCOMING_DIR="$PROJECT_ROOT/incoming/mysql"

# =====================================
# VALIDATE MYSQL SERVICE / INSTALLATION
# =====================================

echo "Checking MySQL installation and service..."
echo

if [ "$CLEANUP_MODE" = "PRESERVE_DATA" ]
then

    if ! dpkg-query -W -f='${Status}' mysql-server \
        2>/dev/null | grep -q "install ok installed"
    then
        echo "ERROR: MySQL Server should remain installed in PRESERVE_DATA mode."
        exit 1
    fi

    if systemctl is-active --quiet mysql
    then
        echo "ERROR: MySQL service should be stopped after PRESERVE_DATA cleanup."
        exit 1
    fi

    echo "MySQL installation preservation validated successfully."
    echo "MySQL service is stopped successfully."

else

    if dpkg-query -W -f='${Status}' mysql-server \
        2>/dev/null | grep -q "install ok installed"
    then
        echo "ERROR: MySQL Server package still exists after DELETE_DATA cleanup."
        exit 1
    fi

    if [ -d "/var/lib/mysql" ]
    then
        echo "ERROR: MySQL data directory still exists after DELETE_DATA cleanup."
        exit 1
    fi

    if [ -d "/etc/mysql" ]
    then
        echo "ERROR: MySQL configuration directory still exists after DELETE_DATA cleanup."
        exit 1
    fi

    echo "MySQL installation removal validated successfully."
    echo "MySQL data removal validated successfully."

fi

# =====================================
# VALIDATE LIQUIBASE XML
# =====================================

echo
echo "Checking MySQL Liquibase XML state..."
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
        echo "ERROR: Generated MySQL Liquibase XML files still exist."
        exit 1
    fi

    if [ ! -f "$MASTER_XML" ]
    then
        echo "ERROR: MySQL master.xml does not exist."
        exit 1
    fi

    echo "MySQL Liquibase XML cleanup validated successfully."

else

    echo "MySQL Liquibase XML preserved in PRESERVE_DATA mode."

fi

# =====================================
# VALIDATE LOAD ARTIFACTS
# =====================================

echo
echo "Checking MySQL load artifacts..."
echo

if [ "$CLEANUP_MODE" = "DELETE_DATA" ]
then

    if [ -f "$HISTORY_FILE" ]
    then
        echo "ERROR: MySQL data load history still exists."
        exit 1
    fi

    if [ -d "$ARCHIVE_DIR" ] && \
       [ -n "$(find "$ARCHIVE_DIR" -mindepth 1 -print -quit)" ]
    then
        echo "ERROR: MySQL archive artifacts still exist."
        exit 1
    fi

    if [ -d "$FAILED_DIR" ] && \
       [ -n "$(find "$FAILED_DIR" -mindepth 1 -print -quit)" ]
    then
        echo "ERROR: MySQL failed artifacts still exist."
        exit 1
    fi

    echo "MySQL load artifacts cleanup validated successfully."

else

    echo "MySQL load artifacts preserved in PRESERVE_DATA mode."

fi

# =====================================
# VALIDATE INCOMING DIRECTORY
# =====================================

echo
echo "Checking incoming source directory..."
echo

if [ -d "$INCOMING_DIR" ]
then
    echo "MySQL incoming source directory preserved."
else
    echo "MySQL incoming source directory does not currently exist."
    echo "No cleanup validation failure required."
fi

# =====================================
# SUCCESS
# =====================================

echo
echo "====================================="
echo "MYSQL CLEANUP VALIDATION SUCCESSFUL"
echo "====================================="
echo
echo "Cleanup Mode : $CLEANUP_MODE"
echo

exit 0