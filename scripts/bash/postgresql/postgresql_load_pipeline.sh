#!/bin/bash

set -e

source "$(dirname "$0")/../common/set_project_root.sh"

cd "$PROJECT_ROOT"

echo
echo "====================================="
echo "POSTGRESQL AUTOMATION PIPELINE"
echo "====================================="
echo

# 1. Validate Python Runtime
bash "$PROJECT_ROOT/scripts/bash/common/validate_python_runtime.sh"

# 2. Validate Python Requirements
bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/validate_python_requirements.sh"

# 3. Start PostgreSQL
bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/start_postgresql.sh"

# 4. Validate PostgreSQL
bash "$PROJECT_ROOT/scripts/bash/postgresql/setup/validate_postgresql.sh"

# 5. Download Dataset
bash "$PROJECT_ROOT/scripts/bash/common/download_dataset.sh"

# 6. Load Data
bash "$PROJECT_ROOT/scripts/bash/postgresql/load/load_data.sh"

# 7. Validate Loaded Data
bash "$PROJECT_ROOT/scripts/bash/postgresql/load/validate_loaded_data.sh"

# 8. Deploy Database Objects (generate + Liquibase deploy)
bash "$PROJECT_ROOT/scripts/bash/postgresql/objects/deploy_objects.sh"

# 9. Validate Database Objects
bash "$PROJECT_ROOT/scripts/bash/postgresql/objects/validate_objects.sh"

# 10. Database Assessment
bash "$PROJECT_ROOT/scripts/bash/postgresql/assessment/run_assessment.sh" all

# 11. Generate Assessment Report
bash "$PROJECT_ROOT/scripts/bash/common/generate_assessment_report.sh"

echo
echo "====================================="
echo "POSTGRESQL AUTOMATION PIPELINE COMPLETED"
echo "====================================="
echo

exit 0
