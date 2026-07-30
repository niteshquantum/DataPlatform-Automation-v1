#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

echo
echo "====================================="
echo "INSTALLING MSSQL JDBC DRIVER"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mssql.conf"

MSSQL_DRIVER_VERSION=$(grep "^MSSQL_DRIVER_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

DRIVER_DIR="$PROJECT_ROOT/tools/drivers"

mkdir -p "$DRIVER_DIR"

JAR_FILE="$DRIVER_DIR/mssql-jdbc-${MSSQL_DRIVER_VERSION}.jre11.jar"

if [ -f "$JAR_FILE" ]
then
    echo "MSSQL Driver already installed"
    echo "$JAR_FILE"
    exit 0
fi

sudo apt-get update
sudo apt-get install -y wget

echo
echo "Downloading MSSQL JDBC Driver ${MSSQL_DRIVER_VERSION}"
echo

wget -O "$JAR_FILE" \
"https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/${MSSQL_DRIVER_VERSION}.jre11/mssql-jdbc-${MSSQL_DRIVER_VERSION}.jre11.jar"

if [ ! -f "$JAR_FILE" ]
then
    echo "MSSQL DRIVER DOWNLOAD FAILED"
    exit 1
fi

echo
echo "Driver Installed:"
echo "$JAR_FILE"

echo
echo "====================================="
echo "MSSQL DRIVER INSTALLED SUCCESSFULLY"
echo "====================================="
echo

exit 0