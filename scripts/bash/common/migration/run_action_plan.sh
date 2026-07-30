#!/bin/bash
set -e

# ============================================================
# GOVERNANCE ACTION PLAN WRAPPER
# ============================================================

if [ -z "$1" ]; then
    echo
    echo "====================================="
    echo "GOVERNANCE ACTION PLAN FAILED"
    echo "====================================="
    echo "Error: Database argument is required."
    echo "Usage: run_action_plan.sh database"
    echo
    exit 1
fi

DATABASE="$1"

echo
echo "====================================="
echo "RUNNING GOVERNANCE ACTION PLAN"
echo "====================================="
echo "Database: ${DATABASE}"
echo

python3 scripts/governance/action_plan_engine.py \
    --database "${DATABASE}"

echo
echo "ACTION PLAN WRAPPER SUCCESSFUL"
echo