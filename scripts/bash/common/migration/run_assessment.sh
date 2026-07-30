#!/bin/bash
set -e

# ============================================================
# MIGRATION ASSESSMENT WRAPPER
# ============================================================

if [ -z "$1" ]; then
    echo
    echo "====================================="
    echo "MIGRATION ASSESSMENT FAILED"
    echo "====================================="
    echo "Error: Database argument is required."
    echo "Usage: run_assessment.sh database"
    echo
    exit 1
fi

DATABASE="$1"

echo
echo "====================================="
echo "RUNNING MIGRATION ASSESSMENT"
echo "====================================="
echo "Database: ${DATABASE}"
echo

python3 scripts/assessment/assessment_engine.py --database "${DATABASE}"

echo
echo "MIGRATION ASSESSMENT WRAPPER SUCCESSFUL"
echo