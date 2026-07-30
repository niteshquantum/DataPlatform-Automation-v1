#!/bin/bash

set -e



source "$(dirname "$0")/../../common/set_project_root.sh"
echo
echo "====================================="
echo "INSTALLING MYSQL DRIVER"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/mysql.conf"

MYSQL_DRIVER_VERSION=$(grep "^MYSQL_DRIVER_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

DRIVER_DIR="$PROJECT_ROOT/tools/drivers"

mkdir -p "$DRIVER_DIR"

JAR_FILE="$DRIVER_DIR/mysql-connector-j-${MYSQL_DRIVER_VERSION}.jar"

if [ -f "$JAR_FILE" ]
then
    echo "MySQL Driver already installed"
    echo "$JAR_FILE"
    exit 0
fi

sudo apt-get update
sudo apt-get install -y wget

echo
echo "Downloading MySQL Connector Version ${MYSQL_DRIVER_VERSION}"
echo

wget -O "$JAR_FILE" "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/${MYSQL_DRIVER_VERSION}/mysql-connector-j-${MYSQL_DRIVER_VERSION}.jar"

if [ ! -f "$JAR_FILE" ]
then
    echo "MYSQL DRIVER DOWNLOAD FAILED"
    exit 1
fi

echo
echo "Driver Installed:"
echo "$JAR_FILE"

echo
echo "====================================="
echo "MYSQL DRIVER INSTALLED SUCCESSFULLY"
echo "====================================="
echo

exit 0