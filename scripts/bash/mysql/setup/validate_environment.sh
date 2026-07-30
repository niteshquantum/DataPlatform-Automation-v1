#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "ENVIRONMENT VALIDATION STARTED"
echo "====================================="
echo

bash "$PROJECT_ROOT/scripts/bash/mysql/setup/validate_port.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/setup/validate_mysql_instance.sh"

echo
echo "====================================="
echo "ENVIRONMENT VALIDATION SUCCESSFUL"
echo "====================================="
echo

exit 0
