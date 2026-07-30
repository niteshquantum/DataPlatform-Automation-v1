#!/bin/bash

set -e

source "$(dirname "$0")/../../common/set_project_root.sh"

echo
echo "====================================="
echo "POSTGRESQL LIQUIBASE XML CLEANUP"
echo "====================================="
echo

# =====================================
# CLEANUP MODE
# =====================================

CLEANUP_MODE="${CLEANUP_MODE:-PRESERVE_DATA}"
CLEANUP_MODE="$(echo "$CLEANUP_MODE" | tr '[:lower:]' '[:upper:]')"

LIQUIBASE_DIR="$PROJECT_ROOT/liquibase/postgresql"
MASTER_XML="$LIQUIBASE_DIR/master.xml"

echo "Cleanup Mode   : $CLEANUP_MODE"
echo "Liquibase Path : $LIQUIBASE_DIR"
echo

# =====================================
# VALIDATE CLEANUP MODE
# =====================================

if [[ "$CLEANUP_MODE" != "PRESERVE_DATA" && \
      "$CLEANUP_MODE" != "DELETE_DATA" ]]
then
    echo "ERROR: Invalid CLEANUP_MODE: $CLEANUP_MODE"
    exit 1
fi

# =====================================
# VALIDATE LIQUIBASE DIRECTORY
# =====================================

if [ ! -d "$LIQUIBASE_DIR" ]
then
    echo "ERROR: PostgreSQL Liquibase directory not found:"
    echo "$LIQUIBASE_DIR"
    exit 1
fi

# =====================================
# PRESERVE DATA MODE
# =====================================

if [ "$CLEANUP_MODE" = "PRESERVE_DATA" ]
then

    echo "PostgreSQL data is being preserved."
    echo "Generated Liquibase XML files will also be preserved."
    echo

    echo "====================================="
    echo "POSTGRESQL LIQUIBASE XML PRESERVED"
    echo "====================================="
    echo

    exit 0
fi

# =====================================
# FIND GENERATED XML FILES
# =====================================

echo "Finding generated Liquibase XML files..."
echo

mapfile -t GENERATED_XML_FILES < <(
    find "$LIQUIBASE_DIR" \
        -maxdepth 1 \
        -type f \
        -name "*.xml" \
        ! -name "master.xml"
)

# =====================================
# REMOVE GENERATED XML FILES
# =====================================

if [ "${#GENERATED_XML_FILES[@]}" -eq 0 ]
then

    echo "No generated Liquibase XML files found."

else

    for XML_FILE in "${GENERATED_XML_FILES[@]}"
    do

        echo "Removing: $(basename "$XML_FILE")"

        rm -f "$XML_FILE"

    done

fi

# =====================================
# RESET MASTER.XML
# =====================================

echo
echo "Resetting master.xml..."
echo

cat > "$MASTER_XML" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>

<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog https://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

</databaseChangeLog>
EOF

# =====================================
# VALIDATE XML CLEANUP
# =====================================

echo "Validating PostgreSQL Liquibase XML cleanup..."
echo

REMAINING_XML_FILES="$(
    find "$LIQUIBASE_DIR" \
        -maxdepth 1 \
        -type f \
        -name "*.xml" \
        ! -name "master.xml" \
        -print -quit
)"

if [ -n "$REMAINING_XML_FILES" ]
then

    echo "ERROR: Generated PostgreSQL Liquibase XML files still exist."
    exit 1

fi

# =====================================
# VALIDATE MASTER.XML
# =====================================

if [ ! -f "$MASTER_XML" ]
then

    echo "ERROR: PostgreSQL master.xml not found after reset."
    exit 1

fi

echo "Generated Liquibase XML files removed successfully."
echo "master.xml reset successfully."

echo
echo "====================================="
echo "POSTGRESQL LIQUIBASE XML CLEANUP SUCCESSFUL"
echo "====================================="
echo

exit 0