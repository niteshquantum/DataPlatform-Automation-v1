#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "REMOVING MYSQL DEPLOYMENT"
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
    echo "MySQL installation will be preserved."
    echo "MySQL database data will be preserved."
    echo

    echo "====================================="
    echo "MYSQL DEPLOYMENT PRESERVED"
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
# CHECK MYSQL INSTALLATION
# =====================================

if ! dpkg-query -W -f='${Status}' mysql-server \
    2>/dev/null | grep -q "install ok installed"
then
    echo "MySQL Server package is not installed."
    echo "Nothing to remove."
    echo

    exit 0
fi

# =====================================
# PURGE MYSQL PACKAGES
# =====================================

echo "Removing MySQL Server packages..."
echo

sudo DEBIAN_FRONTEND=noninteractive \
    apt-get purge -y \
    mysql-server \
    mysql-server-core-* \
    mysql-client \
    mysql-client-core-*

echo
echo "MySQL packages removed successfully."
echo

# =====================================
# REMOVE UNUSED DEPENDENCIES
# =====================================

echo "Removing unused MySQL dependencies..."
echo

sudo DEBIAN_FRONTEND=noninteractive \
    apt-get autoremove -y

echo
echo "Unused dependencies cleanup completed."
echo

# =====================================
# REMOVE MYSQL DATA
# =====================================

echo "Removing MySQL data directory..."
echo

if [ -d "/var/lib/mysql" ]
then
    sudo rm -rf /var/lib/mysql
    echo "MySQL data directory removed successfully."
else
    echo "MySQL data directory already absent."
fi

# =====================================
# REMOVE MYSQL CONFIGURATION
# =====================================

echo
echo "Removing MySQL configuration directory..."
echo

if [ -d "/etc/mysql" ]
then
    sudo rm -rf /etc/mysql
    echo "MySQL configuration directory removed successfully."
else
    echo "MySQL configuration directory already absent."
fi

# =====================================
# VALIDATE REMOVAL
# =====================================

echo
echo "Validating MySQL removal..."
echo

if dpkg-query -W -f='${Status}' mysql-server \
    2>/dev/null | grep -q "install ok installed"
then
    echo "ERROR: MySQL Server package still exists."
    exit 1
fi

if [ -d "/var/lib/mysql" ]
then
    echo "ERROR: MySQL data directory still exists."
    exit 1
fi

echo "MySQL removal validation passed."

echo
echo "====================================="
echo "MYSQL DEPLOYMENT REMOVAL COMPLETE"
echo "====================================="
echo
echo "Cleanup Mode : $CLEANUP_MODE"
echo

exit 0