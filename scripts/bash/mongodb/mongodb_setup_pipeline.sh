#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

bash "$PROJECT_ROOT/scripts/bash/common/validate_python_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/mongodb/setup/install_python_requirements.sh"

bash "$PROJECT_ROOT/scripts/bash/mongodb/setup/validate_python_requirements.sh"

bash "$PROJECT_ROOT/scripts/bash/common/validate_java_runtime.sh"

bash "$PROJECT_ROOT/scripts/bash/mongodb/setup/install_tools.sh"

bash "$PROJECT_ROOT/scripts/bash/mongodb/setup/validate_tools.sh"

bash "$PROJECT_ROOT/scripts/bash/mongodb/setup/install_mongodb.sh"

bash "$PROJECT_ROOT/scripts/bash/mongodb/setup/install_mongosh.sh"

bash "$PROJECT_ROOT/scripts/bash/mongodb/setup/start_mongodb.sh"

bash "$PROJECT_ROOT/scripts/bash/mongodb/setup/validate_mongodb.sh"

echo
echo "====================================="
echo "MONGODB SETUP SUCCESSFUL"
echo "====================================="
echo

exit 0
