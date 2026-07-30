#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "INSTALLING POSTGRESQL DRIVER"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/postgresql.conf"

POSTGRESQL_DRIVER_VERSION=$(grep "^POSTGRESQL_DRIVER_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

DRIVER_DIR="$PROJECT_ROOT/tools/drivers"

mkdir -p "$DRIVER_DIR"

JAR_FILE="$DRIVER_DIR/postgresql-${POSTGRESQL_DRIVER_VERSION}.jar"

if [ -f "$JAR_FILE" ]
then
    echo "PostgreSQL Driver already installed"
    echo "$JAR_FILE"
    exit 0
fi

sudo apt-get update
sudo apt-get install -y wget

echo
echo "Downloading PostgreSQL JDBC Driver Version ${POSTGRESQL_DRIVER_VERSION}"
echo

wget -O "$JAR_FILE" \
"https://repo1.maven.org/maven2/org/postgresql/postgresql/${POSTGRESQL_DRIVER_VERSION}/postgresql-${POSTGRESQL_DRIVER_VERSION}.jar"

if [ ! -f "$JAR_FILE" ]
then
    echo "POSTGRESQL DRIVER DOWNLOAD FAILED"
    exit 1
fi

echo
echo "Driver Installed:"
echo "$JAR_FILE"

echo
echo "====================================="
echo "POSTGRESQL DRIVER INSTALLED SUCCESSFULLY"
echo "====================================="
echo

exit 0