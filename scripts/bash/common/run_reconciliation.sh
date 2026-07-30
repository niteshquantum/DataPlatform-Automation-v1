#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

DATABASE="${1:?Usage: run_reconciliation.sh <database>}"

echo
echo "====================================="
echo "DATA RECONCILIATION"
echo "====================================="
echo

python3 scripts/reconciliation/reconciliation_engine.py --database "$DATABASE"

echo
echo "====================================="
echo "DATA RECONCILIATION COMPLETE"
echo "====================================="
echo

exit 0
