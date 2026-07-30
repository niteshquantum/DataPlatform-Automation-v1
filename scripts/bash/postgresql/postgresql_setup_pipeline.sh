#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

bash "$PROJECT_ROOT/scripts/bash/common/validate_python_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/install_python_requirements.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/validate_python_requirements.sh"

bash "$PROJECT_ROOT/scripts/bash/common/validate_java_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/install_tools.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/deploy_postgresql.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/start_postgresql.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/validate_postgresql.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/create_database.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/run_liquibase.sh"

bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/validate_environment.sh"

echo
echo "====================================="
echo "POSTGRESQL SETUP SUCCESSFUL"
echo "====================================="
echo

exit 0
