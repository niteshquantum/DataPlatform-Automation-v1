#!/bin/bash
set -e

# ============================================================
# COMPLETE MIGRATION ANALYSIS
# ============================================================

if [ -z "$1" ]; then
    echo
    echo "====================================="
    echo "MIGRATION ANALYSIS FAILED"
    echo "====================================="
    echo "Error: Database argument is required."
    echo "Usage: run_migration_analysis.sh database"
    echo
    exit 1
fi

DATABASE="$1"

bash ./scripts/bash/common/migration/run_data_profiling.sh "${DATABASE}"
bash ./scripts/bash/common/migration/run_reconciliation.sh "${DATABASE}"
bash ./scripts/bash/common/migration/run_assessment.sh "${DATABASE}"
bash ./scripts/bash/common/migration/run_recommendation.sh "${DATABASE}"
bash ./scripts/bash/common/migration/run_action_plan.sh "${DATABASE}"
bash ./scripts/bash/common/migration/generate_technical_report.sh "${DATABASE}"
bash ./scripts/bash/common/migration/generate_executive_report.sh "${DATABASE}"

echo
echo "====================================="
echo "MIGRATION ANALYSIS COMPLETED"
echo "====================================="
echo