#!/bin/bash
set -e
source "$(dirname "$0")/../../common/set_project_root.sh"
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT:${PYTHONPATH:-}"
python3 scripts/python/mysql/assessment.py "$@"
