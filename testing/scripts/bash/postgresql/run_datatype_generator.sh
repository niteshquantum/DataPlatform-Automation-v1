#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

cd "$PROJECT_ROOT"

python3 scripts/datatype_registry_generator.py postgresql

exit 0
