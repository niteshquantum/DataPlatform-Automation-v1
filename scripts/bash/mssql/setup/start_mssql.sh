#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "STARTING MSSQL SERVER"
echo "====================================="
echo

SERVICE_NAME="mssql-server"

if [ ! -x "/opt/mssql/bin/sqlservr" ]
then
    echo "MSSQL Server is not installed."
    exit 1
fi

if systemctl is-active --quiet "$SERVICE_NAME"
then
    echo "MSSQL Server is already running."
    echo
    echo "====================================="
    echo "MSSQL SERVER START SUCCESSFUL"
    echo "====================================="
    echo
    exit 0
fi

echo "Enabling MSSQL Server service..."
sudo systemctl enable "$SERVICE_NAME"

echo
echo "Starting MSSQL Server service..."
sudo systemctl start "$SERVICE_NAME"

echo
echo "Waiting for SQL Server to start..."

for i in {1..15}
do
    if systemctl is-active --quiet "$SERVICE_NAME"
    then
        echo
        echo "MSSQL Server started successfully."
        echo
        echo "====================================="
        echo "MSSQL SERVER START SUCCESSFUL"
        echo "====================================="
        echo
        exit 0
    fi

    sleep 2
done

echo
echo "MSSQL SERVER START FAILED"
echo

echo "Service Status:"
sudo systemctl --no-pager --full status "$SERVICE_NAME" || true

exit 1