#!/bin/bash
set -e

# ============================================================
# TECHNICAL REPORT WRAPPER
# ============================================================

if [ -z "$1" ]; then
    echo
    echo "====================================="
    echo "TECHNICAL REPORT GENERATION FAILED"
    echo "====================================="
    echo "Error: Database argument is required."
    echo "Usage: generate_technical_report.sh database"
    echo
    exit 1
fi

DATABASE="$1"

echo
echo "====================================="
echo "GENERATING TECHNICAL MIGRATION REPORT"
echo "====================================="
echo "Database: ${DATABASE}"
echo

python3 scripts/reporting/migration/technical_report.py \
    --database "${DATABASE}"

echo
echo "TECHNICAL REPORT WRAPPER SUCCESSFUL"
echo