#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

cd "$PROJECT_ROOT"

echo
echo "====================================="
echo "MONGODB AUTOMATION PIPELINE"
echo "====================================="
echo

# 1. Validate Python Runtime
bash "$PROJECT_ROOT/scripts/bash/common/validate_python_runtime.sh"

# 2. Install Python Requirements
bash "$PROJECT_ROOT/scripts/bash/mongodb/setup/install_python_requirements.sh"

# 3. Validate Python Requirements
bash "$PROJECT_ROOT/scripts/bash/mongodb/setup/validate_python_requirements.sh"

# 4. Start MongoDB
bash "$PROJECT_ROOT/scripts/bash/mongodb/setup/start_mongodb.sh"

# 5. Validate MongoDB
bash "$PROJECT_ROOT/scripts/bash/mongodb/setup/validate_mongodb.sh"

# 6. Load Data
bash "$PROJECT_ROOT/scripts/bash/mongodb/load/load_data.sh"

# 7. Validate Loaded Data
bash "$PROJECT_ROOT/scripts/bash/mongodb/load/validate_loaded_data.sh"

# 8. Database Assessment (database, collection, index inventories)
bash "$PROJECT_ROOT/scripts/bash/mongodb/assessment/run_assessment.sh" all

# 9. Generate Assessment Report
bash "$PROJECT_ROOT/scripts/bash/common/generate_assessment_report.sh"

echo
echo "====================================="
echo "MONGODB AUTOMATION PIPELINE COMPLETED"
echo "====================================="
echo

exit 0