#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

cd "$PROJECT_ROOT"

echo
echo "====================================="
echo "MSSQL AUTOMATION PIPELINE"
echo "====================================="
echo

bash "$PROJECT_ROOT/scripts/bash/common/validate_python_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/setup/validate_python_requirements.sh"

bash "$PROJECT_ROOT/scripts/bash/common/validate_tools.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/setup/start_mssql.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/setup/validate_mssql.sh"

bash "$PROJECT_ROOT/scripts/bash/common/download_dataset.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/load/load_data.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/load/validate_loaded_data.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/objects/deploy_objects.sh"

bash "$PROJECT_ROOT/scripts/bash/mssql/objects/validate_objects.sh"

echo
echo "====================================="
echo "MSSQL AUTOMATION PIPELINE COMPLETED"
echo "====================================="
echo

exit 0
