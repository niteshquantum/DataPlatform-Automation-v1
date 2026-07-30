#!/bin/bash
set -e

# ============================================================
# DATA PROFILING WRAPPER
# ============================================================

if [ -z "$1" ]; then
    echo
    echo "====================================="
    echo "DATA PROFILING FAILED"
    echo "====================================="
    echo "Error: Database argument is required."
    echo "Usage: run_data_profiling.sh database"
    echo
    exit 1
fi

DATABASE="$1"

echo
echo "====================================="
echo "RUNNING DATA PROFILING"
echo "====================================="
echo "Database: ${DATABASE}"
echo

python3 scripts/profiling/data_profiler.py --database "${DATABASE}"

echo
echo "DATA PROFILING WRAPPER SUCCESSFUL"
echo