#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "INSTALLING POSTGRESQL TOOLS"
echo "====================================="
echo

bash "$PROJECT_ROOT/scripts/bash/common/install_terraform.sh"

bash "$PROJECT_ROOT/scripts/bash/common/install_liquibase.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/install_postgresql_driver.sh"

echo
echo "====================================="
echo "TOOLS INSTALLED SUCCESSFULLY"
echo "====================================="
echo

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/validate_tools.sh"

echo
echo "====================================="
echo "TOOLS VALIDATED SUCCESSFULLY"
echo "====================================="
echo

exit 0