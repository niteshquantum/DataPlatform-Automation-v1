#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

DATABASE="${1:?Usage: run_data_profiling.sh <database>}"

echo
echo "====================================="
echo "DATA PROFILING"
echo "====================================="
echo

python3 scripts/profiling/data_profiler.py --database "$DATABASE"

echo
echo "====================================="
echo "DATA PROFILING COMPLETE"
echo "====================================="
echo

exit 0
