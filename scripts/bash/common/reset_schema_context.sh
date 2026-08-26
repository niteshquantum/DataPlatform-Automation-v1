#!/bin/bash
set -euo pipefail

DATABASE="${1:-}"

if [[ "$DATABASE" != "mysql" && "$DATABASE" != "postgresql" && "$DATABASE" != "mssql" && "$DATABASE" != "mongodb" ]]; then
    echo "[ERROR] reset_schema_context.sh supports mysql, postgresql, mssql, and mongodb." >&2
    exit 1
fi

source "$(dirname "$0")/set_project_root.sh"

log() {
    local timestamp
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $1"
}

get_config_value() {
    local file="$1"
    local key="$2"
    awk -v key="$key" '$0 ~ "^" key "=" { sub("^[^=]*=", ""); print; exit }' "$file"
}

ensure_project_path() {
    local path="$1"
    local resolved_parent

    resolved_parent=$(realpath -m "$(dirname "$path")")
    if [[ "$resolved_parent" != "$PROJECT_ROOT" && "$resolved_parent" != "$PROJECT_ROOT/"* ]]; then
        log "[ERROR] Refusing to reset path outside project root: $path"
        exit 1
    fi
}

CLEANUP_CONFIG_FILE="$PROJECT_ROOT/config/cleanup/ubuntu/$DATABASE.conf"
DATABASE_CONFIG_FILE="$PROJECT_ROOT/config/ubuntu/$DATABASE.conf"

for config_file in "$CLEANUP_CONFIG_FILE" "$DATABASE_CONFIG_FILE"; do
    if [[ ! -f "$config_file" ]]; then
        log "[ERROR] Configuration file not found: $config_file"
        exit 1
    fi
done

reset_mongodb_context_file() {
    local name="$1"
    local relative_path="$2"
    local content="$3"
    local file_path="$PROJECT_ROOT/$relative_path"
    local directory

    ensure_project_path "$file_path"
    directory=$(dirname "$file_path")
    ensure_project_path "$directory"

    log ""
    log "====================================="
    log "RESET $name"
    log "====================================="
    log "Path : $file_path"

    mkdir -p -- "$directory"
    printf '%s\n' "$content" > "$file_path"
    log "Status : RESET SUCCESSFULLY"
}

remove_mongodb_context_file_if_present() {
    local name="$1"
    local relative_path="$2"
    local file_path="$PROJECT_ROOT/$relative_path"

    ensure_project_path "$file_path"

    log ""
    log "====================================="
    log "RESET $name"
    log "====================================="
    log "Path : $file_path"

    if [[ -f "$file_path" ]]; then
        rm -f -- "$file_path"
        log "Status : REMOVED"
    else
        log "Status : NOT FOUND"
        log "Action : SKIPPED - Nothing to reset"
    fi
}

reset_mongodb_schema_context() {
    reset_mongodb_context_file "SCHEMA REGISTRY" "metadata/mongodb/schema_registry.json" '{}'
    reset_mongodb_context_file "DATATYPE REGISTRY" "metadata/mongodb/datatype_registry.json" '{}'
    reset_mongodb_context_file "TABLE SOURCE MAPPING" "metadata/mongodb/table_source_mapping.json" '{}'
    reset_mongodb_context_file "CDC STATUS" "metadata/mongodb/cdc_status.json" '{"tables":{}}'

    remove_mongodb_context_file_if_present "LOAD HISTORY" "metadata/data_load_history.jsonl"

    while IFS='|' read -r name relative_path; do
        remove_mongodb_context_file_if_present "$name" "$relative_path"
    done <<'EOF'
PROFILING METADATA|metadata/profiling/mongodb/profiling.json
RECONCILIATION METADATA|metadata/reconciliation/mongodb/reconciliation.json
DISCOVERY METADATA|metadata/discovery/mongodb/discovery.json
GROWTH ANALYSIS|metadata/discovery/mongodb/growth_analysis.json
DISCOVERY SNAPSHOT|metadata/discovery/mongodb/history/discovery_snapshot.json
REQUIREMENTS ANALYSIS|metadata/discovery/mongodb/requirements_analysis.json
ASSESSMENT METADATA|metadata/assessment/mongodb/assessment.json
RECOMMENDATION METADATA|metadata/recommendation/mongodb/recommendation.json
GOVERNANCE ACTION PLAN|metadata/governance/mongodb/action_plan.json
TECHNICAL MIGRATION REPORT|reports/migration/mongodb/technical_report.html
EXECUTIVE MIGRATION REPORT|reports/migration/mongodb/executive_report.html
EOF
}

if [[ "$DATABASE" == "mongodb" ]]; then
    log ""
    log "============================================================"
    log "RESET SCHEMA CONTEXT"
    log "============================================================"
    log ""
    log "Database      : mongodb"
    log "Project Root  : $PROJECT_ROOT"
    log ""
    log "MongoDB does not use Liquibase or an object registry in this reset flow."

    reset_mongodb_schema_context

    log ""
    log "============================================================"
    log "SCHEMA CONTEXT RESET COMPLETED"
    log "============================================================"
    log ""
    log "Database      : mongodb"
    log "Status        : SUCCESS"
    log ""
    log "NOTE: MongoDB service, database, collections, indexes and data were NOT modified."
    log ""

    exit 0
fi

case "$DATABASE" in
    mysql)
        DATABASE_NAME_KEY="MYSQL_DB"
        ;;
    postgresql)
        DATABASE_NAME_KEY="POSTGRESQL_DB"
        ;;
    mssql)
        DATABASE_NAME_KEY="MSSQL_DB"
        ;;
esac

DATABASE_NAME=$(get_config_value "$DATABASE_CONFIG_FILE" "$DATABASE_NAME_KEY")
if [[ -z "$DATABASE_NAME" ]]; then
    log "[ERROR] Database name not found in configuration key: $DATABASE_NAME_KEY"
    exit 1
fi

LIQUIBASE_ENABLED=$(get_config_value "$CLEANUP_CONFIG_FILE" "LIQUIBASE_ENABLED")
LIQUIBASE_DIR_RELATIVE=$(get_config_value "$CLEANUP_CONFIG_FILE" "LIQUIBASE_DIR")
HISTORY_FILE_RELATIVE=$(get_config_value "$CLEANUP_CONFIG_FILE" "HISTORY_FILE")

log ""
log "============================================================"
log "RESET SCHEMA CONTEXT"
log "============================================================"
log ""
log "Database      : $DATABASE"
log "Database Name : $DATABASE_NAME"
log "Project Root  : $PROJECT_ROOT"
log ""

if [[ "$LIQUIBASE_ENABLED" == "true" ]]; then
    if [[ -z "$LIQUIBASE_DIR_RELATIVE" ]]; then
        log "[ERROR] LIQUIBASE_DIR is required when Liquibase is enabled."
        exit 1
    fi

    LIQUIBASE_DIR="$PROJECT_ROOT/$LIQUIBASE_DIR_RELATIVE"
    ensure_project_path "$LIQUIBASE_DIR"

    log "====================================="
    log "RESET LIQUIBASE CONTEXT"
    log "====================================="
    log "Path : $LIQUIBASE_DIR"

    if [[ ! -d "$LIQUIBASE_DIR" ]]; then
        log "Status : NOT FOUND"
        log "Action : SKIPPED - Nothing to reset"
    else
        mapfile -d '' -t generated_xml_files < <(find "$LIQUIBASE_DIR" -type f -name '*.xml' ! -name 'master.xml' -print0)

        if [[ ${#generated_xml_files[@]} -eq 0 ]]; then
            log "Generated XML files : NONE"
        else
            for xml_file in "${generated_xml_files[@]}"; do
                ensure_project_path "$xml_file"
                log "Removing generated XML : $xml_file"
                rm -f -- "$xml_file"
            done
        fi

        master_xml="$LIQUIBASE_DIR/master.xml"
        ensure_project_path "$master_xml"
        log "Resetting master.xml"
        printf '%s\n' '<?xml version="1.0" encoding="UTF-8"?>' '' '<databaseChangeLog' '    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"' '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"' '    xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog https://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">' '' '</databaseChangeLog>' > "$master_xml"
        log "Status : RESET SUCCESSFULLY"
    fi
else
    log "Liquibase reset disabled for $DATABASE."
fi

if [[ -n "$HISTORY_FILE_RELATIVE" ]]; then
    history_file="$PROJECT_ROOT/$HISTORY_FILE_RELATIVE"
    ensure_project_path "$history_file"
    log ""
    log "====================================="
    log "RESET LOAD HISTORY"
    log "====================================="
    log "Path : $history_file"

    if [[ -f "$history_file" ]]; then
        rm -f -- "$history_file"
        log "Status : RESET SUCCESSFULLY"
    else
        log "Status : NOT FOUND"
        log "Action : SKIPPED - Nothing to reset"
    fi
fi

metadata_dir="$PROJECT_ROOT/metadata/$DATABASE"
ensure_project_path "$metadata_dir"
mkdir -p -- "$metadata_dir"

reset_json_context() {
    local name="$1"
    local file_name="$2"
    local content="$3"
    local file_path="$metadata_dir/$file_name"

    ensure_project_path "$file_path"
    log ""
    log "====================================="
    log "RESET $name"
    log "====================================="
    log "Path : $file_path"

    if [[ -f "$file_path" ]]; then
        log "Existing context found."
        log "Action : Resetting old context"
    else
        log "Status : NOT FOUND"
        log "Action : Creating fresh context"
    fi

    printf '%s\n' "$content" > "$file_path"
    log "Status : RESET SUCCESSFULLY"
}

reset_json_context "OBJECT REGISTRY" "object_registry.json" '{}'
reset_json_context "SCHEMA REGISTRY" "schema_registry.json" '{}'
reset_json_context "TABLE SOURCE MAPPING" "table_source_mapping.json" '{}'
reset_json_context "CDC STATUS" "cdc_status.json" '{"tables":{}}'

log ""
log "============================================================"
log "SCHEMA CONTEXT RESET COMPLETED"
log "============================================================"
log ""
log "Database      : $DATABASE"
log "Database Name : $DATABASE_NAME"
log "Status        : SUCCESS"
log ""
log "NOTE: Actual database, tables and data were NOT modified."

exit 0
