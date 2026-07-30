#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

cd "$PROJECT_ROOT"

echo
echo "====================================="
echo "MYSQL AUTOMATION PIPELINE"
echo "====================================="
echo

bash "$PROJECT_ROOT/scripts/bash/common/validate_python_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/setup/validate_python_requirements.sh"

bash "$PROJECT_ROOT/scripts/bash/common/validate_tools.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/setup/start_mysql.sh"

bash "$PROJECT_ROOT/scripts/bash/common/download_dataset.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/load/validate_csv.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/setup/create_database.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/setup/validate_mysql.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/load/load_data.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/load/validate_loaded_data.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/objects/deploy_objects.sh"

bash "$PROJECT_ROOT/scripts/bash/mysql/objects/validate_objects.sh"

echo
echo "====================================="
echo "MYSQL AUTOMATION PIPELINE COMPLETED"
echo "====================================="
echo

exit 0
