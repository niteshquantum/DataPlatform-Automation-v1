#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

DATABASE="${1:?Usage: run_assessment.sh <database>}"

echo
echo "====================================="
echo "MIGRATION ASSESSMENT"
echo "====================================="
echo

python3 scripts/assessment/assessment_engine.py --database "$DATABASE"

echo
echo "====================================="
echo "MIGRATION ASSESSMENT COMPLETE"
echo "====================================="
echo

exit 0
