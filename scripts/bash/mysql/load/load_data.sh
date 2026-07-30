#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo
echo "====================================="
echo "MYSQL DATA LOAD"
echo "====================================="
echo

echo
echo "-------------------------------------"
echo "DETECTING SCHEMA"
echo "-------------------------------------"
echo

python3 scripts/schema_detector.py mysql

echo
echo "-------------------------------------"
echo "GENERATING LIQUIBASE XML"
echo "-------------------------------------"
echo

python3 scripts/python/mysql/setup/generate_liquibase_xml.py

SCHEMA_STATUS="$PROJECT_ROOT/metadata/mysql/schema_status.json"

SCHEMA_CHANGED=$(python3 -c "
import json
with open('$SCHEMA_STATUS','r') as f:
    print(str(json.load(f)['schema_changed']).lower())
")

echo
echo "-------------------------------------"
echo "UPDATING MASTER XML"
echo "-------------------------------------"
echo

rm -f "$PROJECT_ROOT/liquibase/mysql/master.xml"

python3 scripts/python/mysql/setup/update_master_xml.py

echo
echo "-------------------------------------"
echo "SCHEMA DECISION"
echo "-------------------------------------"
echo

LOAD_REQUIRED=false

if [ "$SCHEMA_CHANGED" = "true" ]; then

    echo "Schema changes detected."
    echo "Running Liquibase..."

    bash "$PROJECT_ROOT/scripts/bash/mysql/setup/run_liquibase.sh"

    LOAD_REQUIRED=true

else

    echo "No schema changes detected."
    echo "Running CDC..."

    # Temporarily disable 'exit on error'
    set +e
    python3 scripts/cdc/cdc_engine.py mysql
    CDC_EXIT=$?
    set -e

    case $CDC_EXIT in

        0)
            echo "Data changes detected."
            LOAD_REQUIRED=true
            ;;

        100)
            echo "No data changes detected."
            LOAD_REQUIRED=false
            ;;

        *)
            echo "CDC execution failed."
            exit $CDC_EXIT
            ;;

    esac

fi

if [ "$LOAD_REQUIRED" = "true" ]; then

    echo
    echo "-------------------------------------"
    echo "LOADING DATA"
    echo "-------------------------------------"
    echo

    if [ "$SCHEMA_CHANGED" = "true" ]; then
        export LOAD_MODE=full
    else
        export LOAD_MODE=incremental
    fi

    echo "LOAD MODE : $LOAD_MODE"

    python3 scripts/data_loader.py mysql

else

    echo
    echo "-------------------------------------"
    echo "SKIPPING DATA LOAD"
    echo "-------------------------------------"
    echo

fi

echo
echo "-------------------------------------"
echo "VALIDATING DATA"
echo "-------------------------------------"
echo

python3 scripts/python/mysql/load/validate_data.py

echo
echo "====================================="
echo "MYSQL LOAD PIPELINE COMPLETED"
echo "====================================="
echo

exit 0