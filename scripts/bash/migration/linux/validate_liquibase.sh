#!/bin/bash
set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING MIGRATION LIQUIBASE"
echo "====================================="
echo

DB_TYPE="${1^^}"

if [ -z "$DB_TYPE" ]
then
    echo "ERROR: Database type not provided"
    echo "Usage: validate_liquibase.sh <DB_TYPE>"
    exit 1
fi

CONFIG_FILE="$PROJECT_ROOT/config/linux/migration/${DB_TYPE}.conf"

if [ ! -f "$CONFIG_FILE" ]
then
    echo "ERROR: MIGRATION CONFIG NOT FOUND"
    echo "Expected: $CONFIG_FILE"
    exit 1
fi

EXPECTED_VERSION=""

while IFS='=' read -r KEY VALUE
do
    KEY="${KEY#"${KEY%%[![:space:]]*}"}"
    KEY="${KEY%"${KEY##*[![:space:]]}"}"
    VALUE="${VALUE#"${VALUE%%[![:space:]]*}"}"
    VALUE="${VALUE%"${VALUE##*[![:space:]]}"}"

    if [ "$KEY" = "LIQUIBASE_VERSION" ]
    then
        EXPECTED_VERSION="$VALUE"
    fi
done < "$CONFIG_FILE"

if [ -z "$EXPECTED_VERSION" ]
then
    echo "ERROR: LIQUIBASE_VERSION NOT FOUND IN CONFIG"
    exit 1
fi

LIQUIBASE_HOME="$PROJECT_ROOT/tools/liquibase"
LIQUIBASE_BIN="$LIQUIBASE_HOME/liquibase"

if [ ! -d "$LIQUIBASE_HOME" ]
then
    echo "ERROR: LIQUIBASE DIRECTORY NOT FOUND"
    echo "Expected: $LIQUIBASE_HOME"
    exit 1
fi

if [ ! -f "$LIQUIBASE_BIN" ]
then
    echo "ERROR: LIQUIBASE EXECUTABLE NOT FOUND"
    echo "Expected: $LIQUIBASE_BIN"
    exit 1
fi

echo "Expected Liquibase Version : $EXPECTED_VERSION"
echo

if [ -n "$JAVA_HOME" ] && [ -x "$JAVA_HOME/bin/java" ]
then
    echo "Java Found:"
    echo "$JAVA_HOME"
    echo
    "$JAVA_HOME/bin/java" -version
else
    echo "Java Found:"
    which java
    echo
    java -version
fi

echo

LIQUIBASE_VERSION_FILE=$(mktemp)
"$LIQUIBASE_BIN" --version > "$LIQUIBASE_VERSION_FILE" 2>&1 || true
cat "$LIQUIBASE_VERSION_FILE"
echo

DETECTED_VERSION=$(grep -oE "Liquibase Version: [0-9]+\.[0-9]+\.[0-9]+" "$LIQUIBASE_VERSION_FILE" | cut -d' ' -f3 || true)
rm -f "$LIQUIBASE_VERSION_FILE"

if [ -n "$DETECTED_VERSION" ] && [ "$DETECTED_VERSION" != "$EXPECTED_VERSION" ]
then
    echo "ERROR: LIQUIBASE VERSION MISMATCH"
    echo "Expected : $EXPECTED_VERSION"
    echo "Detected : $DETECTED_VERSION"
    exit 1
fi

echo.
echo "====================================="
echo "MIGRATION LIQUIBASE VALIDATED"
echo "====================================="
echo.

exit 0
