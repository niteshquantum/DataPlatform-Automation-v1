#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "VALIDATING POSTGRESQL ENVIRONMENT"
echo "====================================="
echo

bash "$PROJECT_ROOT/scripts/bash/common/validate_python_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/validate_python_requirements.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/validate_tools.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/validate_port.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/validate_postgresql.sh"

echo
echo "====================================="
echo "POSTGRESQL ENVIRONMENT VALIDATED"
echo "====================================="
echo

exit 0