#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

DATABASE="${1:?Usage: generate_executive_report.sh <database>}"

echo
echo "====================================="
echo "EXECUTIVE MIGRATION REPORT"
echo "====================================="
echo

python3 scripts/reporting/migration/executive_report.py --database "$DATABASE"

echo
echo "====================================="
echo "EXECUTIVE MIGRATION REPORT COMPLETE"
echo "====================================="
echo

exit 0
