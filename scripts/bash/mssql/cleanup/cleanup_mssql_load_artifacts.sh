#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "MSSQL LOAD ARTIFACTS CLEANUP"
echo "====================================="
echo

# =====================================
# CLEANUP MODE
# =====================================

CLEANUP_MODE="${CLEANUP_MODE:-PRESERVE_DATA}"
CLEANUP_MODE="$(echo "$CLEANUP_MODE" | tr '[:lower:]' '[:upper:]')"

HISTORY_FILE="$PROJECT_ROOT/metadata/mssql/data_load_history.jsonl"
ARCHIVE_DIR="$PROJECT_ROOT/archive/mssql"
FAILED_DIR="$PROJECT_ROOT/failed/mssql"
INCOMING_DIR="$PROJECT_ROOT/incoming/mssql"

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

    echo "MSSQL data is being preserved."
    echo "Load history, archive and failed artifacts will also be preserved."
    echo "Incoming source files will remain untouched."
    echo

    echo "====================================="
    echo "MSSQL LOAD ARTIFACTS PRESERVED"
    echo "====================================="
    echo

    exit 0
fi

# =====================================
# CLEAN DATA LOAD HISTORY
# =====================================

echo "Cleaning MSSQL data load history..."

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
echo "Cleaning MSSQL archive artifacts..."

if [ -d "$ARCHIVE_DIR" ]
then

    find "$ARCHIVE_DIR" \
        -mindepth 1 \
        -maxdepth 1 \
        -exec rm -rf -- {} +

    echo "MSSQL archive artifacts removed successfully."

else

    echo "MSSQL archive directory not found. Nothing to remove."

fi

# =====================================
# CLEAN FAILED ARTIFACTS
# =====================================

echo
echo "Cleaning MSSQL failed artifacts..."

if [ -d "$FAILED_DIR" ]
then

    find "$FAILED_DIR" \
        -mindepth 1 \
        -maxdepth 1 \
        -exec rm -rf -- {} +

    echo "MSSQL failed artifacts removed successfully."

else

    echo "MSSQL failed directory not found. Nothing to remove."

fi

# =====================================
# VALIDATE CLEANUP
# =====================================

echo
echo "Validating MSSQL load artifacts cleanup..."
echo

if [ -f "$HISTORY_FILE" ]
then
    echo "ERROR: MSSQL data load history still exists."
    exit 1
fi

if [ -d "$ARCHIVE_DIR" ] && \
   [ -n "$(find "$ARCHIVE_DIR" -mindepth 1 -print -quit)" ]
then
    echo "ERROR: MSSQL archive artifacts still exist."
    exit 1
fi

if [ -d "$FAILED_DIR" ] && \
   [ -n "$(find "$FAILED_DIR" -mindepth 1 -print -quit)" ]
then
    echo "ERROR: MSSQL failed artifacts still exist."
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
echo "MSSQL LOAD ARTIFACTS CLEANUP SUCCESSFUL"
echo "====================================="
echo

exit 0