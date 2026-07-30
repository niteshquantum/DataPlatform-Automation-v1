#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

echo
echo "====================================="
echo "STARTING SQL SERVER"
echo "====================================="
echo

sudo systemctl start mssql-server

sleep 10

if ! sudo systemctl is-active --quiet mssql-server
then
    echo "SQL Server failed to start"
    exit 1
fi

echo "SQL Server Service Running"

echo
echo "====================================="
echo "SQL SERVER STARTED SUCCESSFULLY"
echo "====================================="
echo

exit 0