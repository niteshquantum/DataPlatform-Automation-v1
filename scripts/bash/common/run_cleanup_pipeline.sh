#!/bin/bash
set -euo pipefail

CLEANUP_MODE="${1:-}"
DATABASE="${2:-}"

if [[ -z "$CLEANUP_MODE" ]]; then
    echo "[ERROR] Missing required argument: cleanupMode" >&2
    exit 1
fi

if [[ -z "$DATABASE" ]]; then
    echo "[ERROR] Missing required argument: database" >&2
    exit 1
fi

source "$(dirname "$0")/set_project_root.sh"

log() {
    local timestamp
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    echo "[$timestamp] $1"
}

log ""
log "====================================="
log "CLEANUP ORCHESTRATOR"
log "====================================="
log ""
log "Database     : $DATABASE"
log "Cleanup Mode : $CLEANUP_MODE"
log "Project Root : $PROJECT_ROOT"
log ""

case "$CLEANUP_MODE" in
    PRESERVE_DATA|DELETE_DATA)
        ;;
    *)
        log "[ERROR] Invalid cleanup mode: $CLEANUP_MODE"
        log "Allowed values: PRESERVE_DATA, DELETE_DATA"
        exit 1
        ;;
esac

get_config_value() {
    local file="$1"
    local key="$2"
    if [[ ! -f "$file" ]]; then
        echo ""
        return
    fi
    grep -E "^${key}=" "$file" | head -n 1 | cut -d'=' -f2-
}

COMMON_CONFIG_FILE="$PROJECT_ROOT/config/cleanup/cleanup.conf"
OS_CONFIG_FILE="$PROJECT_ROOT/config/cleanup/ubuntu/os.conf"
DB_CONFIG_FILE="$PROJECT_ROOT/config/cleanup/ubuntu/$DATABASE.conf"

if [[ ! -f "$COMMON_CONFIG_FILE" ]]; then
    log "[ERROR] Common cleanup config not found: $COMMON_CONFIG_FILE"
    exit 1
fi

if [[ ! -f "$OS_CONFIG_FILE" ]]; then
    log "[ERROR] OS cleanup config not found: $OS_CONFIG_FILE"
    exit 1
fi

if [[ ! -f "$DB_CONFIG_FILE" ]]; then
    log "[ERROR] Database cleanup config not found: $DB_CONFIG_FILE"
    exit 1
fi

XML_CLEANUP_ENABLED=$(get_config_value "$DB_CONFIG_FILE" "XML_CLEANUP_ENABLED")
CLEANUP_DATA_ENABLED=$(get_config_value "$DB_CONFIG_FILE" "CLEANUP_DATA_ENABLED_UBUNTU")
DROP_DATABASE_ENABLED=$(get_config_value "$DB_CONFIG_FILE" "DROP_DATABASE_ENABLED_UBUNTU")

export CLEANUP_MODE

DB_LOWER=$(echo "$DATABASE" | tr '[:upper:]' '[:lower:]')

STOP_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/stop_$DB_LOWER.sh"

case "$DB_LOWER" in
    mysql)
        REMOVE_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/remove_mysql.sh"
        TERRAFORM_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/reset_terraform_state.sh"
        ARTIFACTS_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/cleanup_mysql_load_artifacts.sh"
        XML_SCRIPT=""
        if [[ "$XML_CLEANUP_ENABLED" == "true" ]]; then
            XML_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/cleanup_mysql_xml.sh"
        fi
        VALIDATE_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/validate_cleanup.sh"
        DATA_SCRIPT=""
        if [[ "$DB_LOWER" == "mysql" && "$CLEANUP_DATA_ENABLED" == "true" ]]; then
            if [[ -f "$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/cleanup_mysql_data.sh" ]]; then
                DATA_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/cleanup_mysql_data.sh"
            fi
        fi
        DROP_SCRIPT=""
        ;;
    mssql)
        REMOVE_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/remove_mssql.sh"
        TERRAFORM_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/reset_terraform_state.sh"
        ARTIFACTS_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/cleanup_mssql_load_artifacts.sh"
        XML_SCRIPT=""
        if [[ "$XML_CLEANUP_ENABLED" == "true" ]]; then
            XML_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/cleanup_mssql_xml.sh"
        fi
        VALIDATE_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/validate_cleanup.sh"
        DATA_SCRIPT=""
        DROP_SCRIPT=""
        if [[ "$DROP_DATABASE_ENABLED" == "true" ]]; then
            if [[ -f "$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/drop_mssql_database.sh" ]]; then
                DROP_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/drop_mssql_database.sh"
            fi
        fi
        ;;
    postgresql)
        REMOVE_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/remove_postgresql.sh"
        TERRAFORM_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/reset_terraform_state.sh"
        ARTIFACTS_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/cleanup_postgresql_load_artifacts.sh"
        XML_SCRIPT=""
        if [[ "$XML_CLEANUP_ENABLED" == "true" ]]; then
            XML_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/cleanup_postgresql_xml.sh"
        fi
        VALIDATE_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/validate_cleanup.sh"
        DATA_SCRIPT=""
        DROP_SCRIPT=""
        ;;
    mongodb)
        REMOVE_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/remove_mongodb.sh"
        TERRAFORM_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/reset_terraform_state.sh"
        ARTIFACTS_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/cleanup_mongodb_load_artifacts.sh"
        XML_SCRIPT=""
        VALIDATE_SCRIPT="$PROJECT_ROOT/scripts/bash/$DB_LOWER/cleanup/validate_cleanup.sh"
        DATA_SCRIPT=""
        DROP_SCRIPT=""
        ;;
esac

STEPS=()

if [[ -n "$DROP_SCRIPT" ]]; then
    STEPS+=("DROP DATABASE|$DROP_SCRIPT")
fi

STEPS+=("STOP SERVICE|$STOP_SCRIPT")

if [[ -n "$DATA_SCRIPT" ]]; then
    STEPS+=("CLEANUP DATA|$DATA_SCRIPT")
fi

STEPS+=("REMOVE DEPLOYMENT|$REMOVE_SCRIPT")
STEPS+=("RESET TERRAFORM|$TERRAFORM_SCRIPT")

if [[ -n "$XML_SCRIPT" ]]; then
    STEPS+=("CLEANUP XML|$XML_SCRIPT")
fi

STEPS+=("CLEANUP ARTIFACTS|$ARTIFACTS_SCRIPT")
STEPS+=("VALIDATE|$VALIDATE_SCRIPT")

step_number=0
for step_entry in "${STEPS[@]}"; do
    step_number=$((step_number + 1))
    step_name="${step_entry%%|*}"
    step_script="${step_entry##*|}"

    log ""
    log "====================================="
    log "STEP $step_number - $step_name"
    log "====================================="
    log ""

    if [[ ! -f "$step_script" ]]; then
        log "[ERROR] Script not found: $step_script"
        exit 1
    fi

    bash "$step_script"
    step_exit=$?
    if [[ $step_exit -ne 0 ]]; then
        log ""
        log "[ERROR] Step failed: $step_name (exit $step_exit)"
        exit $step_exit
    fi
done

log ""
log "====================================="
log "$DB_LOWER CLEANUP COMPLETED"
log "====================================="
log ""
log "Cleanup Mode : $CLEANUP_MODE"
log "Status       : SUCCESS"
log ""

exit 0
