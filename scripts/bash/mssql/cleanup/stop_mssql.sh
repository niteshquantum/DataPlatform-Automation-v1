#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "STOPPING MSSQL SERVER"
echo "====================================="
echo

# =====================================
# CHECK MSSQL INSTALLATION
# =====================================

if [ ! -x "/opt/mssql/bin/sqlservr" ]
then
    echo "MSSQL Server is not installed."
    echo "Nothing to stop."
    echo

    echo "====================================="
    echo "MSSQL STOP SUCCESSFUL"
    echo "====================================="
    echo

    exit 0
fi

# =====================================
# CHECK SERVICE
# =====================================

if ! systemctl list-unit-files mssql-server.service \
    >/dev/null 2>&1
then
    echo "MSSQL Server service does not exist."
    echo "Nothing to stop."
    echo

    echo "====================================="
    echo "MSSQL STOP SUCCESSFUL"
    echo "====================================="
    echo

    exit 0
fi

# =====================================
# STOP MSSQL SERVER
# =====================================

if systemctl is-active --quiet mssql-server
then

    echo "MSSQL Server service is running."
    echo "Stopping MSSQL Server..."
    echo

    sudo systemctl stop mssql-server

else

    echo "MSSQL Server service is already stopped."

fi

# =====================================
# WAIT FOR SERVICE TO STOP
# =====================================

echo
echo "Waiting for MSSQL Server to stop..."
echo

STOPPED=false

for i in {1..30}
do

    if ! systemctl is-active --quiet mssql-server
    then
        STOPPED=true
        break
    fi

    sleep 1

done

# =====================================
# VALIDATE STOP
# =====================================

if [ "$STOPPED" = false ]
then
    echo "ERROR: MSSQL Server failed to stop."
    exit 1
fi

if systemctl is-active --quiet mssql-server
then
    echo "ERROR: MSSQL Server service is still running."
    exit 1
fi

echo "MSSQL Server service validation passed."

echo
echo "====================================="
echo "MSSQL STOP SUCCESSFUL"
echo "====================================="
echo

exit 0