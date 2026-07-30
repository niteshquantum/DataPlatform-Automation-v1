#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

DATABASE="${1:?Usage: generate_technical_report.sh <database>}"

echo
echo "====================================="
echo "TECHNICAL MIGRATION REPORT"
echo "====================================="
echo

python3 scripts/reporting/migration/technical_report.py --database "$DATABASE"

echo
echo "====================================="
echo "TECHNICAL MIGRATION REPORT COMPLETE"
echo "====================================="
echo

exit 0
