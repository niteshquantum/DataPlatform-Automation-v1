#!/bin/bash
set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

CLEANUP_MODE="${CLEANUP_MODE:-PRESERVE_DATA}"
CLEANUP_MODE="$(echo "$CLEANUP_MODE" | tr '[:lower:]' '[:upper:]')"

echo
echo "====================================="
echo "POSTGRESQL CLEANUP PIPELINE"
echo "====================================="
echo

if [[ "$CLEANUP_MODE" != "PRESERVE_DATA" && "$CLEANUP_MODE" != "DELETE_DATA" ]]; then
    echo "ERROR: Invalid CLEANUP_MODE: $CLEANUP_MODE" >&2
    echo "Valid cleanup modes: PRESERVE_DATA, DELETE_DATA" >&2
    exit 1
fi

echo "Project Root : $PROJECT_ROOT"
echo "Cleanup Mode : $CLEANUP_MODE"
echo

bash "$PROJECT_ROOT/scripts/bash/common/run_cleanup_pipeline.sh" "$CLEANUP_MODE" "postgresql"

echo
echo "====================================="
echo "POSTGRESQL CLEANUP PIPELINE COMPLETED"
echo "====================================="
echo
echo "Project Root : $PROJECT_ROOT"
echo "Cleanup Mode : $CLEANUP_MODE"
echo "Status       : SUCCESS"
echo

exit 0
