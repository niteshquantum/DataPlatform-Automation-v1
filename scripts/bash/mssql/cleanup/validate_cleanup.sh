#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING MSSQL CLEANUP"
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

MSSQL_SERVER="/opt/mssql/bin/sqlservr"
MSSQL_DATA_DIR="/var/opt/mssql"
SQLCMD_EXE="/opt/mssql-tools18/bin/sqlcmd"
SQLCMD_LINK="/usr/local/bin/sqlcmd"

LIQUIBASE_DIR="$PROJECT_ROOT/liquibase/mssql"
MASTER_XML="$LIQUIBASE_DIR/master.xml"

HISTORY_FILE="$PROJECT_ROOT/metadata/mssql/data_load_history.jsonl"
ARCHIVE_DIR="$PROJECT_ROOT/archive/mssql"
FAILED_DIR="$PROJECT_ROOT/failed/mssql"
INCOMING_DIR="$PROJECT_ROOT/incoming/mssql"

# =====================================
# VALIDATE PRESERVE DATA MODE
# =====================================

if [ "$CLEANUP_MODE" = "PRESERVE_DATA" ]
then

    echo "Validating PRESERVE_DATA cleanup..."
    echo

    # MSSQL installation must exist

    if [ ! -x "$MSSQL_SERVER" ]
    then
        echo "ERROR: MSSQL Server installation was not preserved."
        exit 1
    fi

    echo "MSSQL Server installation preserved successfully."

    # MSSQL service must be stopped

    if systemctl is-active --quiet mssql-server
    then
        echo "ERROR: MSSQL Server service is still running."
        exit 1
    fi

    echo "MSSQL Server service is stopped successfully."

    # MSSQL data must exist

    if [ ! -d "$MSSQL_DATA_DIR" ]
    then
        echo "ERROR: MSSQL data directory was not preserved."
        exit 1
    fi

    echo "MSSQL data directory preserved successfully."

    # MSSQL tools must exist

    if [ ! -x "$SQLCMD_EXE" ]
    then
        echo "ERROR: MSSQL sqlcmd tool was not preserved."
        exit 1
    fi

    echo "MSSQL tools preserved successfully."

    echo
    echo "MSSQL Liquibase XML preserved in PRESERVE_DATA mode."
    echo "MSSQL load artifacts preserved in PRESERVE_DATA mode."

fi

# =====================================
# VALIDATE DELETE DATA MODE
# =====================================

if [ "$CLEANUP_MODE" = "DELETE_DATA" ]
then

    echo "Validating DELETE_DATA cleanup..."
    echo

    # =====================================
    # VALIDATE MSSQL PACKAGE
    # =====================================

    if dpkg-query -W -f='${Status}' \
        mssql-server 2>/dev/null |
        grep -q "install ok installed"
    then
        echo "ERROR: MSSQL Server package still exists."
        exit 1
    fi

    echo "MSSQL Server package removal validated successfully."

    # =====================================
    # VALIDATE MSSQL DATA
    # =====================================

    if [ -d "$MSSQL_DATA_DIR" ]
    then
        echo "ERROR: MSSQL data directory still exists."
        exit 1
    fi

    echo "MSSQL data removal validated successfully."

    # =====================================
    # VALIDATE MSSQL TOOLS
    # =====================================

    for PACKAGE in \
        mssql-tools18 \
        msodbcsql18 \
        unixodbc-dev
    do

        if dpkg-query -W -f='${Status}' \
            "$PACKAGE" 2>/dev/null |
            grep -q "install ok installed"
        then
            echo "ERROR: MSSQL tools package still exists: $PACKAGE"
            exit 1
        fi

    done

    echo "MSSQL tools removal validated successfully."

    # =====================================
    # VALIDATE SQLCMD LINK
    # =====================================

    if [ -L "$SQLCMD_LINK" ]
    then

        LINK_TARGET="$(readlink -f "$SQLCMD_LINK" || true)"

        if [ "$LINK_TARGET" = "$SQLCMD_EXE" ]
        then
            echo "ERROR: Project-configured SQLCMD link still exists."
            exit 1
        fi

    fi

    echo "SQLCMD global link cleanup validated successfully."

    # =====================================
    # VALIDATE LIQUIBASE XML
    # =====================================

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
        echo "ERROR: Generated MSSQL Liquibase XML files still exist."
        exit 1
    fi

    if [ ! -f "$MASTER_XML" ]
    then
        echo "ERROR: MSSQL master.xml does not exist."
        exit 1
    fi

    echo "MSSQL Liquibase XML cleanup validated successfully."

    # =====================================
    # VALIDATE LOAD HISTORY
    # =====================================

    if [ -f "$HISTORY_FILE" ]
    then
        echo "ERROR: MSSQL data load history still exists."
        exit 1
    fi

    # =====================================
    # VALIDATE ARCHIVE
    # =====================================

    if [ -d "$ARCHIVE_DIR" ] && \
       [ -n "$(find "$ARCHIVE_DIR" -mindepth 1 -print -quit)" ]
    then
        echo "ERROR: MSSQL archive artifacts still exist."
        exit 1
    fi

    # =====================================
    # VALIDATE FAILED ARTIFACTS
    # =====================================

    if [ -d "$FAILED_DIR" ] && \
       [ -n "$(find "$FAILED_DIR" -mindepth 1 -print -quit)" ]
    then
        echo "ERROR: MSSQL failed artifacts still exist."
        exit 1
    fi

    echo "MSSQL load artifacts cleanup validated successfully."

fi

# =====================================
# VALIDATE INCOMING DIRECTORY
# =====================================

echo
echo "Checking incoming source directory..."
echo

if [ -d "$INCOMING_DIR" ]
then
    echo "MSSQL incoming source directory preserved."
else
    echo "MSSQL incoming source directory does not currently exist."
    echo "No cleanup validation failure required."
fi

# =====================================
# SUCCESS
# =====================================

echo
echo "====================================="
echo "MSSQL CLEANUP VALIDATION SUCCESSFUL"
echo "====================================="
echo
echo "Cleanup Mode : $CLEANUP_MODE"
echo

exit 0