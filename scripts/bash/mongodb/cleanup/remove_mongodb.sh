#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "REMOVING PROJECT-MANAGED MONGODB"
echo "====================================="
echo

# =====================================
# PATHS
# =====================================

MONGO_HOME="$PROJECT_ROOT/databases/mongodb"

SERVER_DIR="$MONGO_HOME/server"
MONGOSH_DIR="$MONGO_HOME/mongosh"
DATA_DIR="$MONGO_HOME/data"
LOGS_DIR="$MONGO_HOME/logs"
CONFIG_DIR="$MONGO_HOME/config"

echo "Project Root : $PROJECT_ROOT"
echo "Mongo Home   : $MONGO_HOME"
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

echo "Cleanup Mode : $CLEANUP_MODE"
echo

# =====================================
# SAFETY VALIDATION
# =====================================

EXPECTED_MONGO_HOME="$PROJECT_ROOT/databases/mongodb"

if [ "$MONGO_HOME" != "$EXPECTED_MONGO_HOME" ]
then
    echo "ERROR: MongoDB cleanup safety validation failed."
    exit 1
fi

# =====================================
# IDEMPOTENCY CHECK
# =====================================

if [ ! -d "$MONGO_HOME" ]
then
    echo "MongoDB deployment directory does not exist."
    echo "Nothing to remove."
    echo

    echo "====================================="
    echo "MONGODB REMOVAL SUCCESSFUL"
    echo "====================================="
    echo

    exit 0
fi

# =====================================
# REMOVE PROJECT PATH FUNCTION
# =====================================

remove_project_path() {

    local PATH_TO_REMOVE="$1"
    local DESCRIPTION="$2"

    if [ -e "$PATH_TO_REMOVE" ]
    then

        echo "Removing $DESCRIPTION..."
        echo "Path : $PATH_TO_REMOVE"

        rm -rf -- "$PATH_TO_REMOVE"

        if [ -e "$PATH_TO_REMOVE" ]
        then
            echo "ERROR: Failed to remove $DESCRIPTION"
            echo "Path : $PATH_TO_REMOVE"
            exit 1
        fi

        echo "$DESCRIPTION removed successfully."

    else

        echo "$DESCRIPTION already absent. Skipping."

    fi

    echo
}

# =====================================
# PRESERVE DATA MODE
# =====================================

if [ "$CLEANUP_MODE" = "PRESERVE_DATA" ]
then

    echo "Applying PRESERVE_DATA cleanup..."
    echo

    remove_project_path \
        "$SERVER_DIR" \
        "MongoDB server deployment"

    remove_project_path \
        "$MONGOSH_DIR" \
        "mongosh deployment"

    remove_project_path \
        "$LOGS_DIR" \
        "MongoDB runtime logs"

    remove_project_path \
        "$CONFIG_DIR" \
        "MongoDB runtime configuration"

    echo "MongoDB data directory preserved."

    if [ -f "$MONGO_HOME/mongodb.tgz" ]
    then
        echo "MongoDB download cache preserved."
    fi

    if [ -f "$MONGO_HOME/mongosh.tgz" ]
    then
        echo "mongosh download cache preserved."
    fi

    echo
    echo "====================================="
    echo "MONGODB DEPLOYMENT PRESERVED"
    echo "====================================="
    echo

    exit 0
fi

# =====================================
# DELETE DATA MODE
# =====================================

echo "Applying DELETE_DATA cleanup..."
echo

remove_project_path \
    "$MONGO_HOME" \
    "complete project-managed MongoDB deployment"

# =====================================
# FINAL VALIDATION
# =====================================

if [ -e "$MONGO_HOME" ]
then
    echo "ERROR: MongoDB deployment directory still exists."
    exit 1
fi

echo
echo "====================================="
echo "MONGODB DEPLOYMENT REMOVAL COMPLETE"
echo "====================================="
echo
echo "Cleanup Mode : $CLEANUP_MODE"
echo

exit 0