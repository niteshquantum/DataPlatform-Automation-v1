#!/bin/bash
set -e

# ============================================================
# EXECUTIVE REPORT WRAPPER
# ============================================================

if [ -z "$1" ]; then
    echo
    echo "====================================="
    echo "EXECUTIVE REPORT GENERATION FAILED"
    echo "====================================="
    echo "Error: Database argument is required."
    echo "Usage: generate_executive_report.sh database"
    echo
    exit 1
fi

DATABASE="$1"

echo
echo "====================================="
echo "GENERATING EXECUTIVE MIGRATION REPORT"
echo "====================================="
echo "Database: ${DATABASE}"
echo

python3 scripts/reporting/migration/executive_report.py \
    --database "${DATABASE}"

echo
echo "EXECUTIVE REPORT WRAPPER SUCCESSFUL"
echo