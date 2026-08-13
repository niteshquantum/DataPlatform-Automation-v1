#!/bin/bash
set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "RUNNING MIGRATION LIQUIBASE"
echo "====================================="
echo

DB_TYPE="${1^^}"
CHANGELOG="${2:-liquibase/migration/${DB_TYPE,,}/master.xml}"
LB_COMMAND="${3:-update}"

if [ -z "$DB_TYPE" ]
then
    echo "ERROR: Database type not provided"
    echo "Usage: run_liquibase.sh <DB_TYPE> [CHANGELOG] [LB_COMMAND] [HOST PORT DB USER PASSWORD]"
    exit 1
fi

CONFIG_FILE="$PROJECT_ROOT/config/linux/migration/${DB_TYPE,,}.conf"

if [ ! -f "$CONFIG_FILE" ]
then
    echo "ERROR: MIGRATION CONFIG NOT FOUND"
    echo "Expected: $CONFIG_FILE"
    exit 1
fi

DB_HOST=""
DB_PORT=""
DB_NAME=""
DB_USER=""
DB_PASSWORD=""
DB_DRIVER_VERSION=""
DB_ODBC_DRIVER=""
EXPECTED_LIQUIBASE_VERSION=""

while IFS='=' read -r KEY VALUE
do
    KEY="${KEY#"${KEY%%[![:space:]]*}"}"
    KEY="${KEY%"${KEY##*[![:space:]]}"}"
    VALUE="${VALUE#"${VALUE%%[![:space:]]*}"}"
    VALUE="${VALUE%"${VALUE##*[![:space:]]}"}"

    case "$KEY" in
        "${DB_TYPE}_HOST") DB_HOST="$VALUE" ;;
        "${DB_TYPE}_PORT") DB_PORT="$VALUE" ;;
        "${DB_TYPE}_DB") DB_NAME="$VALUE" ;;
        "${DB_TYPE}_USER") DB_USER="$VALUE" ;;
        "${DB_TYPE}_PASSWORD") DB_PASSWORD="$VALUE" ;;
        "${DB_TYPE}_DRIVER_VERSION") DB_DRIVER_VERSION="$VALUE" ;;
        "${DB_TYPE}_ODBC_DRIVER") DB_ODBC_DRIVER="$VALUE" ;;
        "LIQUIBASE_VERSION") EXPECTED_LIQUIBASE_VERSION="$VALUE" ;;
    esac
done < "$CONFIG_FILE"

if [ -n "$4" ]
then
    DB_HOST="$4"
fi

if [ -n "$5" ]
then
    DB_PORT="$5"
fi

if [ -n "$6" ]
then
    DB_NAME="$6"
fi

if [ -n "$7" ]
then
    DB_USER="$7"
fi

if [ -n "$8" ]
then
    DB_PASSWORD="$8"
fi

if [ -z "$DB_HOST" ]
then
    echo "ERROR: ${DB_TYPE}_HOST NOT FOUND"
    echo "Provide via argument or migration config file."
    exit 1
fi

if [ -z "$DB_PORT" ]
then
    echo "ERROR: ${DB_TYPE}_PORT NOT FOUND"
    echo "Provide via argument or migration config file."
    exit 1
fi

if [ -z "$DB_NAME" ]
then
    echo "ERROR: ${DB_TYPE}_DB NOT FOUND"
    echo "Provide via argument or migration config file."
    exit 1
fi

if [ -z "$DB_USER" ]
then
    echo "ERROR: ${DB_TYPE}_USER NOT FOUND"
    echo "Provide via argument or migration config file."
    exit 1
fi

if [ -z "$DB_DRIVER_VERSION" ]
then
    echo "ERROR: ${DB_TYPE}_DRIVER_VERSION NOT FOUND IN MIGRATION CONFIG"
    echo "File: $CONFIG_FILE"
    exit 1
fi

echo
echo "====================================="
echo "VALIDATING LIQUIBASE"
echo "====================================="
echo

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

echo "Expected Liquibase Version : $EXPECTED_LIQUIBASE_VERSION"
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

if [ -n "$EXPECTED_LIQUIBASE_VERSION" ]
then
    LIQUIBASE_VERSION_FILE=$(mktemp)
    "$LIQUIBASE_BIN" --version > "$LIQUIBASE_VERSION_FILE" 2>&1 || true
    DETECTED_VERSION=$(grep -oE "Liquibase Version: [0-9]+\.[0-9]+\.[0-9]+" "$LIQUIBASE_VERSION_FILE" | cut -d' ' -f3 || true)
    rm -f "$LIQUIBASE_VERSION_FILE"

    if [ -n "$DETECTED_VERSION" ] && [ "$DETECTED_VERSION" != "$EXPECTED_LIQUIBASE_VERSION" ]
    then
        echo "ERROR: LIQUIBASE VERSION MISMATCH"
        echo "Expected : $EXPECTED_LIQUIBASE_VERSION"
        echo "Detected : $DETECTED_VERSION"
        exit 1
    fi
fi

echo "====================================="
echo "LIQUIBASE VALIDATED"
echo "====================================="
echo

echo
echo "====================================="
echo "VALIDATING ${DB_TYPE} JDBC DRIVER"
echo "====================================="
echo

DRIVER_DIR="$PROJECT_ROOT/tools/drivers"

if [ ! -d "$DRIVER_DIR" ]
then
    echo "ERROR: DRIVER DIRECTORY NOT FOUND"
    echo "Expected: $DRIVER_DIR"
    exit 1
fi

if [ "$DB_TYPE" = "MSSQL" ]
then
    EXPECTED_DRIVER="$DRIVER_DIR/mssql-jdbc-${DB_DRIVER_VERSION}.jre11.jar"
elif [ "$DB_TYPE" = "MYSQL" ]
then
    EXPECTED_DRIVER="$DRIVER_DIR/mysql-connector-j-${DB_DRIVER_VERSION}.jar"
elif [ "$DB_TYPE" = "POSTGRESQL" ]
then
    EXPECTED_DRIVER="$DRIVER_DIR/postgresql-${DB_DRIVER_VERSION}.jar"
else
    echo "ERROR: Unsupported database type for driver validation: $DB_TYPE"
    exit 1
fi

if [ ! -f "$EXPECTED_DRIVER" ]
then
    echo "ERROR: EXPECTED JDBC DRIVER NOT FOUND"
    echo "Expected: $EXPECTED_DRIVER"
    exit 1
fi

echo "Driver Found:"
echo "$EXPECTED_DRIVER"
echo.
echo "====================================="
echo "${DB_TYPE} JDBC DRIVER VALIDATED"
echo "====================================="
echo.

cd "$PROJECT_ROOT"

if [ ! -f "$CHANGELOG" ]
then
    echo "ERROR: CHANGELOG NOT FOUND"
    echo "Expected: $PROJECT_ROOT/$CHANGELOG"
    exit 1
fi

echo
echo "Database : $DB_TYPE"
echo "Host     : $DB_HOST"
echo "Port     : $DB_PORT"
echo "DB       : $DB_NAME"
echo "User     : $DB_USER"
echo "Driver   : $EXPECTED_DRIVER"
echo "Changelog: $CHANGELOG"
echo

if [ "$DB_TYPE" = "MSSQL" ]
then
    JDBC_URL="jdbc:sqlserver://${DB_HOST}:${DB_PORT};databaseName=${DB_NAME};encrypt=true;trustServerCertificate=true"
    DRIVER_CLASS="com.microsoft.sqlserver.jdbc.SQLServerDriver"
elif [ "$DB_TYPE" = "MYSQL" ]
then
    JDBC_URL="jdbc:mysql://${DB_HOST}:${DB_PORT}/${DB_NAME}"
    DRIVER_CLASS="com.mysql.cj.jdbc.Driver"
elif [ "$DB_TYPE" = "POSTGRESQL" ]
then
    JDBC_URL="jdbc:postgresql://${DB_HOST}:${DB_PORT}/${DB_NAME}"
    DRIVER_CLASS="org.postgresql.Driver"
else
    echo "ERROR: Unsupported database type: $DB_TYPE"
    exit 1
fi

PASSWORD_OPTION=()

if [ -n "$DB_PASSWORD" ]
then
    PASSWORD_OPTION=(--password="$DB_PASSWORD")
fi

"$LIQUIBASE_BIN" \
    --classpath="$EXPECTED_DRIVER" \
    --driver="$DRIVER_CLASS" \
    --search-path="$PROJECT_ROOT" \
    --changeLogFile="$CHANGELOG" \
    --url="$JDBC_URL" \
    --username="$DB_USER" \
    "${PASSWORD_OPTION[@]}" \
    "$LB_COMMAND"

echo
echo "====================================="
echo "${DB_TYPE} LIQUIBASE ${LB_COMMAND} COMPLETED"
echo "====================================="
echo

exit 0
