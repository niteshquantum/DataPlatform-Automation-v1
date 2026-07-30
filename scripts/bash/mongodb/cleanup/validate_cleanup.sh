#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING MONGODB CLEANUP"
echo "====================================="
echo

# =====================================
# CLEANUP MODE
# =====================================

CLEANUP_MODE="${CLEANUP_MODE:-PRESERVE_DATA}"
CLEANUP_MODE="$(echo "$CLEANUP_MODE" | tr '[:lower:]' '[:upper:]')"

if [[ "$CLEANUP_MODE" != "PRESERVE_DATA" && \
      "$CLEANUP_MODE" != "DELETE_DATA" ]]
then
    echo "ERROR: Invalid CLEANUP_MODE: $CLEANUP_MODE"
    exit 1
fi

# =====================================
# PATHS
# =====================================

MONGO_HOME="$PROJECT_ROOT/databases/mongodb"

SERVER_DIR="$MONGO_HOME/server"
MONGOSH_DIR="$MONGO_HOME/mongosh"
DATA_DIR="$MONGO_HOME/data"
LOGS_DIR="$MONGO_HOME/logs"
CONFIG_DIR="$MONGO_HOME/config"

HISTORY_FILE="$PROJECT_ROOT/metadata/mongodb/data_load_history.jsonl"
ARCHIVE_DIR="$PROJECT_ROOT/archive/mongodb"
FAILED_DIR="$PROJECT_ROOT/failed/mongodb"
INCOMING_DIR="$PROJECT_ROOT/incoming/mongodb"

echo "Project Root : $PROJECT_ROOT"
echo "Mongo Home   : $MONGO_HOME"
echo "Cleanup Mode : $CLEANUP_MODE"
echo

# =====================================
# VALIDATE MONGODB PROCESS
# =====================================

echo "Checking project-managed MongoDB process..."
echo

MONGOD_EXE="$SERVER_DIR/bin/mongod"

if [ -x "$MONGOD_EXE" ]
then

    RUNNING_PIDS="$(
        pgrep -f "$MONGOD_EXE" 2>/dev/null || true
    )"

    if [ -n "$RUNNING_PIDS" ]
    then
        echo "ERROR: Project-managed MongoDB process is still running."
        echo "PID(s): $RUNNING_PIDS"
        exit 1
    fi

fi

echo "MongoDB process cleanup validated successfully."

# =====================================
# PRESERVE DATA VALIDATION
# =====================================

if [ "$CLEANUP_MODE" = "PRESERVE_DATA" ]
then

    echo
    echo "Validating PRESERVE_DATA cleanup..."
    echo

    if [ -d "$SERVER_DIR" ]
    then
        echo "ERROR: MongoDB server deployment still exists."
        exit 1
    fi

    if [ -d "$MONGOSH_DIR" ]
    then
        echo "ERROR: mongosh deployment still exists."
        exit 1
    fi

    if [ -d "$LOGS_DIR" ]
    then
        echo "ERROR: MongoDB logs directory still exists."
        exit 1
    fi

    if [ -d "$CONFIG_DIR" ]
    then
        echo "ERROR: MongoDB configuration directory still exists."
        exit 1
    fi

    if [ ! -d "$DATA_DIR" ]
    then
        echo "ERROR: MongoDB data directory was not preserved."
        exit 1
    fi

    echo "MongoDB server deployment removal validated successfully."
    echo "mongosh deployment removal validated successfully."
    echo "MongoDB runtime artifacts removal validated successfully."
    echo "MongoDB data preservation validated successfully."

fi

# =====================================
# DELETE DATA VALIDATION
# =====================================

if [ "$CLEANUP_MODE" = "DELETE_DATA" ]
then

    echo
    echo "Validating DELETE_DATA cleanup..."
    echo

    if [ -e "$MONGO_HOME" ]
    then
        echo "ERROR: MongoDB deployment directory still exists."
        exit 1
    fi

    echo "Complete MongoDB deployment removal validated successfully."

fi

# =====================================
# VALIDATE LOAD ARTIFACTS
# =====================================

echo
echo "Checking MongoDB load artifacts..."
echo

if [ "$CLEANUP_MODE" = "DELETE_DATA" ]
then

    if [ -f "$HISTORY_FILE" ]
    then
        echo "ERROR: MongoDB data load history still exists."
        exit 1
    fi

    if [ -d "$ARCHIVE_DIR" ] && \
       [ -n "$(find "$ARCHIVE_DIR" -mindepth 1 -print -quit)" ]
    then
        echo "ERROR: MongoDB archive artifacts still exist."
        exit 1
    fi

    if [ -d "$FAILED_DIR" ] && \
       [ -n "$(find "$FAILED_DIR" -mindepth 1 -print -quit)" ]
    then
        echo "ERROR: MongoDB failed artifacts still exist."
        exit 1
    fi

    echo "MongoDB load artifacts cleanup validated successfully."

else

    echo "MongoDB load artifacts preserved in PRESERVE_DATA mode."

fi

# =====================================
# VALIDATE INCOMING DIRECTORY
# =====================================

echo
echo "Checking incoming source directory..."
echo

if [ -d "$INCOMING_DIR" ]
then
    echo "MongoDB incoming source directory preserved."
else
    echo "MongoDB incoming source directory does not currently exist."
    echo "No cleanup validation failure required."
fi

# =====================================
# SUCCESS
# =====================================

echo
echo "====================================="
echo "MONGODB CLEANUP VALIDATION SUCCESSFUL"
echo "====================================="
echo
echo "Cleanup Mode : $CLEANUP_MODE"
echo

exit 0