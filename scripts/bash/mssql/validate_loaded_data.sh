#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

python3 "$PROJECT_ROOT/scripts/python/mssql/validate_loaded_data.py"