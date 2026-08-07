#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

cd "$PROJECT_ROOT"

if [ "${SCHEMA_SOURCE}" = "DATABASE" ]; then
    python3 scripts/schema_extractor.py mysql
else
    python3 scripts/schema_detector.py mysql
fi

exit 0
