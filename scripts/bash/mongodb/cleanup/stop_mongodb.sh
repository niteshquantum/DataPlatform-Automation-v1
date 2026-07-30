#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "STOPPING MONGODB SERVER"
echo "====================================="
echo

MONGO_HOME="$PROJECT_ROOT/databases/mongodb"
MONGOD_EXE="$MONGO_HOME/server/bin/mongod"

echo "Project Root : $PROJECT_ROOT"
echo "Mongo Home   : $MONGO_HOME"
echo

# =====================================
# CHECK PROJECT-MANAGED MONGOD PROCESS
# =====================================

echo "Checking project-managed MongoDB process..."
echo

MONGOD_PIDS=""

if [ -x "$MONGOD_EXE" ]
then
    MONGOD_PIDS="$(
        pgrep -f "$MONGOD_EXE" 2>/dev/null || true
    )"
fi

# =====================================
# STOP MONGODB
# =====================================

if [ -z "$MONGOD_PIDS" ]
then
    echo "Project-managed MongoDB process is not running."
    echo "Nothing to stop."
else

    for PID in $MONGOD_PIDS
    do
        echo "Stopping project-managed MongoDB process..."
        echo "PID : $PID"

        kill "$PID" 2>/dev/null || true
    done

    # =====================================
    # WAIT FOR PROCESS TO STOP
    # =====================================

    STOPPED=false

    for i in {1..30}
    do
        REMAINING_PIDS="$(
            pgrep -f "$MONGOD_EXE" 2>/dev/null || true
        )"

        if [ -z "$REMAINING_PIDS" ]
        then
            STOPPED=true
            break
        fi

        sleep 1
    done

    # =====================================
    # FORCE STOP IF REQUIRED
    # =====================================

    if [ "$STOPPED" = false ]
    then
        echo
        echo "MongoDB process did not stop gracefully."
        echo "Force stopping project-managed MongoDB process..."

        REMAINING_PIDS="$(
            pgrep -f "$MONGOD_EXE" 2>/dev/null || true
        )"

        for PID in $REMAINING_PIDS
        do
            kill -9 "$PID" 2>/dev/null || true
        done

        sleep 2
    fi

fi

# =====================================
# FINAL VALIDATION
# =====================================

echo
echo "Validating MongoDB process status..."
echo

REMAINING_PIDS="$(
    pgrep -f "$MONGOD_EXE" 2>/dev/null || true
)"

if [ -n "$REMAINING_PIDS" ]
then
    echo "ERROR: Project-managed MongoDB process is still running."
    echo "PID(s): $REMAINING_PIDS"
    exit 1
fi

echo "MongoDB process validation passed."

echo
echo "====================================="
echo "MONGODB STOP SUCCESSFUL"
echo "====================================="
echo

exit 0