#!/bin/bash
set -e

# ============================================================
# RECOMMENDATION ENGINE WRAPPER
# ============================================================

if [ -z "$1" ]; then
    echo
    echo "====================================="
    echo "RECOMMENDATION ENGINE FAILED"
    echo "====================================="
    echo "Error: Database argument is required."
    echo "Usage: run_recommendation.sh database"
    echo
    exit 1
fi

DATABASE="$1"

echo
echo "====================================="
echo "RUNNING RECOMMENDATION ENGINE"
echo "====================================="
echo "Database: ${DATABASE}"
echo

python3 scripts/recommendation/recommendation_engine.py \
    --database "${DATABASE}"

echo
echo "RECOMMENDATION ENGINE WRAPPER SUCCESSFUL"
echo