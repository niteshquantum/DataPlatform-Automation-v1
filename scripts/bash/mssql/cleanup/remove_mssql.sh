#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "REMOVING MSSQL DEPLOYMENT"
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
# PRESERVE DATA MODE
# =====================================

if [ "$CLEANUP_MODE" = "PRESERVE_DATA" ]
then

    echo "Applying PRESERVE_DATA cleanup..."
    echo
    echo "MSSQL Server installation will be preserved."
    echo "MSSQL database data will be preserved."
    echo "MSSQL tools will be preserved."
    echo

    echo "====================================="
    echo "MSSQL DEPLOYMENT PRESERVED"
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
# REMOVE SQLCMD GLOBAL LINK
# =====================================

echo "Checking SQLCMD global link..."
echo

if [ -L "/usr/local/bin/sqlcmd" ]
then

    LINK_TARGET="$(readlink -f /usr/local/bin/sqlcmd || true)"

    if [ "$LINK_TARGET" = "/opt/mssql-tools18/bin/sqlcmd" ]
    then
        echo "Removing project-configured SQLCMD global link..."

        sudo rm -f /usr/local/bin/sqlcmd

        echo "SQLCMD global link removed successfully."
    else
        echo "SQLCMD link points to another installation."
        echo "Skipping removal for safety."
    fi

else

    echo "Project-configured SQLCMD global link does not exist."
    echo "Nothing to remove."

fi

# =====================================
# REMOVE MSSQL SERVER PACKAGE
# =====================================

echo
echo "Checking MSSQL Server package..."
echo

if dpkg-query -W -f='${Status}' \
    mssql-server 2>/dev/null |
    grep -q "install ok installed"
then

    echo "Removing MSSQL Server package..."
    echo

    sudo DEBIAN_FRONTEND=noninteractive \
        apt-get purge -y mssql-server

    echo
    echo "MSSQL Server package removed successfully."

else

    echo "MSSQL Server package is not installed."
    echo "Nothing to remove."

fi

# =====================================
# REMOVE MSSQL TOOLS
# =====================================

echo
echo "Checking MSSQL tools packages..."
echo

TOOLS_TO_REMOVE=()

for PACKAGE in \
    mssql-tools18 \
    msodbcsql18 \
    unixodbc-dev
do

    if dpkg-query -W -f='${Status}' \
        "$PACKAGE" 2>/dev/null |
        grep -q "install ok installed"
    then
        TOOLS_TO_REMOVE+=("$PACKAGE")
    fi

done

if [ "${#TOOLS_TO_REMOVE[@]}" -gt 0 ]
then

    echo "Removing MSSQL tools packages..."
    echo

    sudo DEBIAN_FRONTEND=noninteractive \
        apt-get purge -y "${TOOLS_TO_REMOVE[@]}"

    echo
    echo "MSSQL tools packages removed successfully."

else

    echo "MSSQL tools packages are already absent."

fi

# =====================================
# REMOVE UNUSED DEPENDENCIES
# =====================================

echo
echo "Removing unused dependencies..."
echo

sudo DEBIAN_FRONTEND=noninteractive \
    apt-get autoremove -y

echo
echo "Unused dependencies cleanup completed."

# =====================================
# REMOVE MSSQL DATA
# =====================================

MSSQL_DATA_DIR="/var/opt/mssql"

echo
echo "Checking MSSQL data directory..."
echo "Path : $MSSQL_DATA_DIR"
echo

if [ -d "$MSSQL_DATA_DIR" ]
then

    echo "Removing MSSQL data directory..."

    sudo rm -rf "$MSSQL_DATA_DIR"

    echo "MSSQL data directory removed successfully."

else

    echo "MSSQL data directory already absent."

fi

# =====================================
# VALIDATE SERVER REMOVAL
# =====================================

echo
echo "Validating MSSQL removal..."
echo

if dpkg-query -W -f='${Status}' \
    mssql-server 2>/dev/null |
    grep -q "install ok installed"
then
    echo "ERROR: MSSQL Server package still exists."
    exit 1
fi

if [ -d "$MSSQL_DATA_DIR" ]
then
    echo "ERROR: MSSQL data directory still exists."
    exit 1
fi

if [ -L "/usr/local/bin/sqlcmd" ]
then

    REMAINING_LINK_TARGET="$(
        readlink -f /usr/local/bin/sqlcmd || true
    )"

    if [ "$REMAINING_LINK_TARGET" = "/opt/mssql-tools18/bin/sqlcmd" ]
    then
        echo "ERROR: Project-configured SQLCMD global link still exists."
        exit 1
    fi

fi

echo "MSSQL removal validation passed."

echo
echo "====================================="
echo "MSSQL DEPLOYMENT REMOVAL COMPLETE"
echo "====================================="
echo
echo "Cleanup Mode : $CLEANUP_MODE"
echo

exit 0