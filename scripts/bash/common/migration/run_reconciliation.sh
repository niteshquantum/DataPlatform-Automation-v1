#!/bin/bash
set -e

# ============================================================
# DATA RECONCILIATION WRAPPER
# ============================================================

if [ -z "$1" ]; then
    echo
    echo "====================================="
    echo "DATA RECONCILIATION FAILED"
    echo "====================================="
    echo "Error: Database argument is required."
    echo "Usage: run_reconciliation.sh database"
    echo
    exit 1
fi

DATABASE="$1"

echo
echo "====================================="
echo "RUNNING DATA RECONCILIATION"
echo "====================================="
echo "Database: ${DATABASE}"
echo

python3 scripts/reconciliation/reconciliation_engine.py --database "${DATABASE}"

echo
echo "DATA RECONCILIATION WRAPPER SUCCESSFUL"
echo