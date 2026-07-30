#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

DATABASE="${1:?Usage: run_action_plan.sh <database>}"

echo
echo "====================================="
echo "GOVERNANCE ACTION PLAN"
echo "====================================="
echo

python3 scripts/governance/action_plan_engine.py --database "$DATABASE"

echo
echo "====================================="
echo "GOVERNANCE ACTION PLAN COMPLETE"
echo "====================================="
echo

exit 0
