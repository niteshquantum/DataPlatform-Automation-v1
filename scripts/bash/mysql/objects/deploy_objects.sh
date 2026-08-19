#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

cd "$PROJECT_ROOT"

export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

echo
echo "====================================="
echo "MYSQL OBJECTS DEPLOYMENT"
echo "====================================="
echo

python3 scripts/python/common/objects/bootstrap_generator.py mysql

# Keep this evidence adjacent to generation and Liquibase execution.  The
# deployment must not continue if the generated changeset lacks its targeted
# existing-index reconciliation precondition.
INDEX_XML="$PROJECT_ROOT/liquibase/mysql/objects/generated/indexes/001_idx_products_product_id.xml"
INDEX_SQL="$PROJECT_ROOT/liquibase/mysql/objects/generated/indexes/001_idx_products_product_id.sql"
MASTER_OBJECTS_XML="$PROJECT_ROOT/liquibase/mysql/master_objects.xml"

echo "=== MYSQL OBJECT DEPLOYMENT GIT STATE ==="
git rev-parse HEAD
git branch --show-current

echo "=== GENERATED MYSQL INDEX XML ==="
if [ ! -f "$INDEX_XML" ]; then
    echo "ERROR: Expected generated index changelog is missing: $INDEX_XML"
    exit 1
fi
if [ ! -f "$INDEX_SQL" ]; then
    echo "ERROR: Expected generated index SQL is missing: $INDEX_SQL"
    exit 1
fi
sed -n '1,120p' "$INDEX_XML"

echo "=== SEARCH INDEX XML COPIES ==="
find "$PROJECT_ROOT" -name "001_idx_products_product_id.xml" -print

echo "=== SEARCH INDEX REFERENCES ==="
grep -R -n --include='*.xml' "idx_products_product_id" "$PROJECT_ROOT/liquibase/mysql" || true

echo "=== MASTER OBJECTS XML ==="
if [ ! -f "$MASTER_OBJECTS_XML" ]; then
    echo "ERROR: Generated master objects changelog is missing: $MASTER_OBJECTS_XML"
    exit 1
fi
sed -n '1,160p' "$MASTER_OBJECTS_XML"

for EXPECTED_TEXT in \
    'onFail="MARK_RAN"' \
    'onError="HALT"' \
    '<sqlCheck expectedResult="0">' \
    'information_schema.STATISTICS' \
    'TABLE_SCHEMA = DATABASE()' \
    "TABLE_NAME = 'products'" \
    "INDEX_NAME = 'idx_products_product_id'" \
    'liquibase/mysql/objects/generated/indexes/001_idx_products_product_id.sql'
do
    if ! grep -Fq "$EXPECTED_TEXT" "$INDEX_XML"; then
        echo "ERROR: Generated index changelog is missing: $EXPECTED_TEXT"
        exit 1
    fi
done

if ! grep -Fq 'objects/generated/indexes/001_idx_products_product_id.xml' "$MASTER_OBJECTS_XML"; then
    echo "ERROR: master_objects.xml does not include the generated products index changelog"
    exit 1
fi

python3 scripts/python/common/objects/deploy_objects.py mysql

echo
echo "====================================="
echo "MYSQL OBJECTS DEPLOYMENT SUCCESSFUL"
echo "====================================="
echo

exit 0
