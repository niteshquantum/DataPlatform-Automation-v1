#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "MYSQL LOAD ARTIFACTS CLEANUP"
echo "====================================="
echo

# =====================================
# CLEANUP MODE
# =====================================

CLEANUP_MODE="${CLEANUP_MODE:-PRESERVE_DATA}"
CLEANUP_MODE="$(echo "$CLEANUP_MODE" | tr '[:lower:]' '[:upper:]')"

HISTORY_FILE="$PROJECT_ROOT/metadata/mysql/data_load_history.jsonl"
ARCHIVE_DIR="$PROJECT_ROOT/archive/mysql"
FAILED_DIR="$PROJECT_ROOT/failed/mysql"
INCOMING_DIR="$PROJECT_ROOT/incoming/mysql"

echo "Cleanup Mode  : $CLEANUP_MODE"
echo "History File  : $HISTORY_FILE"
echo "Archive Path  : $ARCHIVE_DIR"
echo "Failed Path   : $FAILED_DIR"
echo "Incoming Path : $INCOMING_DIR"
echo

# =====================================
# VALIDATE CLEANUP MODE
# =====================================

if [[ "$CLEANUP_MODE" != "PRESERVE_DATA" && \
      "$CLEANUP_MODE" != "DELETE_DATA" ]]
then
    echo "ERROR: Invalid CLEANUP_MODE: $CLEANUP_MODE"
    exit 1
fi

# =====================================
# PRESERVE DATA MODE
# =====================================

if [ "$CLEANUP_MODE" = "PRESERVE_DATA" ]
then
    echo "MySQL data is being preserved."
    echo "Load history, archive and failed artifacts will also be preserved."
    echo "Incoming source files will remain untouched."
    echo

    echo "====================================="
    echo "MYSQL LOAD ARTIFACTS PRESERVED"
    echo "====================================="
    echo

    exit 0
fi

# =====================================
# CLEAN DATA LOAD HISTORY
# =====================================

echo "Cleaning MySQL data load history..."

if [ -f "$HISTORY_FILE" ]
then
    rm -f "$HISTORY_FILE"

    echo "Data load history removed successfully."
else
    echo "Data load history not found. Nothing to remove."
fi

# =====================================
# CLEAN ARCHIVE ARTIFACTS
# =====================================

echo
echo "Cleaning MySQL archive artifacts..."

if [ -d "$ARCHIVE_DIR" ]
then

    find "$ARCHIVE_DIR" \
        -mindepth 1 \
        -maxdepth 1 \
        -exec rm -rf -- {} +

    echo "MySQL archive artifacts removed successfully."

else
    echo "MySQL archive directory not found. Nothing to remove."
fi

# =====================================
# CLEAN FAILED ARTIFACTS
# =====================================

echo
echo "Cleaning MySQL failed artifacts..."

if [ -d "$FAILED_DIR" ]
then

    find "$FAILED_DIR" \
        -mindepth 1 \
        -maxdepth 1 \
        -exec rm -rf -- {} +

    echo "MySQL failed artifacts removed successfully."

else
    echo "MySQL failed directory not found. Nothing to remove."
fi

# =====================================
# VALIDATE LOAD HISTORY CLEANUP
# =====================================

echo
echo "Validating MySQL load artifacts cleanup..."
echo

if [ -f "$HISTORY_FILE" ]
then
    echo "ERROR: MySQL data load history still exists."
    exit 1
fi

# =====================================
# VALIDATE ARCHIVE CLEANUP
# =====================================

if [ -d "$ARCHIVE_DIR" ] && \
   [ -n "$(find "$ARCHIVE_DIR" -mindepth 1 -print -quit)" ]
then
    echo "ERROR: MySQL archive artifacts still exist."
    exit 1
fi

# =====================================
# VALIDATE FAILED CLEANUP
# =====================================

if [ -d "$FAILED_DIR" ] && \
   [ -n "$(find "$FAILED_DIR" -mindepth 1 -print -quit)" ]
then
    echo "ERROR: MySQL failed artifacts still exist."
    exit 1
fi

# =====================================
# SUCCESS
# =====================================

echo "Data load history cleanup validated successfully."
echo "Archive cleanup validated successfully."
echo "Failed artifacts cleanup validated successfully."
echo "Incoming source files preserved."

echo
echo "====================================="
echo "MYSQL LOAD ARTIFACTS CLEANUP SUCCESSFUL"
echo "====================================="
echo

exit 0