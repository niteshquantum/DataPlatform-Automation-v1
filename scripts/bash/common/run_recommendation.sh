#!/bin/bash

set -e

source "$(dirname "$0")/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"

DATABASE="${1:?Usage: run_recommendation.sh <database>}"

echo
echo "====================================="
echo "MIGRATION RECOMMENDATIONS"
echo "====================================="
echo

python3 scripts/recommendation/recommendation_engine.py --database "$DATABASE"

echo
echo "====================================="
echo "MIGRATION RECOMMENDATIONS COMPLETE"
echo "====================================="
echo

exit 0
