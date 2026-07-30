#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING POSTGRESQL JDBC DRIVER"
echo "====================================="
echo

CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/postgresql.conf"

if [ ! -f "$CONFIG_FILE" ]
then
    echo "POSTGRESQL CONFIG NOT FOUND"
    echo "Expected: $CONFIG_FILE"
    exit 1
fi

POSTGRESQL_DRIVER_VERSION=$(grep "^POSTGRESQL_DRIVER_VERSION=" "$CONFIG_FILE" | cut -d'=' -f2)

if [ -z "$POSTGRESQL_DRIVER_VERSION" ]
then
    echo "POSTGRESQL_DRIVER_VERSION NOT FOUND IN postgresql.conf"
    exit 1
fi

echo "Expected Driver Version : $POSTGRESQL_DRIVER_VERSION"
echo

DRIVER_DIR="$PROJECT_ROOT/tools/drivers"

if [ ! -d "$DRIVER_DIR" ]
then
    echo "DRIVER DIRECTORY NOT FOUND"
    echo "Expected: $DRIVER_DIR"
    exit 1
fi

EXPECTED_JAR="$DRIVER_DIR/postgresql-${POSTGRESQL_DRIVER_VERSION}.jar"

if [ ! -f "$EXPECTED_JAR" ]
then
    echo "EXPECTED JDBC DRIVER NOT FOUND"
    echo "Expected: $EXPECTED_JAR"
    exit 1
fi

echo "Driver Found:"
echo "$EXPECTED_JAR"

echo
echo "====================================="
echo "POSTGRESQL JDBC DRIVER VALIDATED"
echo "====================================="
echo

exit 0