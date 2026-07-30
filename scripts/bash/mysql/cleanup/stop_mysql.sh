#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "STOPPING MYSQL SERVER"
echo "====================================="
echo

# =====================================
# CHECK MYSQL SERVICE
# =====================================

if ! systemctl list-unit-files mysql.service \
    >/dev/null 2>&1
then
    echo "MySQL service does not exist."
    echo "Nothing to stop."
    echo

    exit 0
fi

# =====================================
# STOP MYSQL
# =====================================

if systemctl is-active --quiet mysql
then
    echo "MySQL service is running."
    echo "Stopping MySQL service..."
    echo

    sudo systemctl stop mysql
else
    echo "MySQL service is already stopped."
fi

# =====================================
# VALIDATE SERVICE STATUS
# =====================================

echo
echo "Validating MySQL service status..."
echo

if systemctl is-active --quiet mysql
then
    echo "ERROR: MySQL service is still running."
    exit 1
fi

echo "MySQL service validation passed."

echo
echo "====================================="
echo "MYSQL STOP SUCCESSFUL"
echo "====================================="
echo

exit 0