#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "ENVIRONMENT VALIDATION STARTED"
echo "====================================="
echo

bash "$PROJECT_ROOT/scripts/bash/common/validate_python_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/common/validate_java_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/setup/validate_tools.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/setup/validate_port.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/setup/validate_mssql.sh"

echo
echo "====================================="
echo "ENVIRONMENT VALIDATION SUCCESSFUL"
echo "====================================="
echo

exit 0