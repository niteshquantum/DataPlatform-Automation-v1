# Windows Migration Pipeline — Local Testing Flow

## Pipeline Stages

```
Initialize
   ↓
Validate Source
   ↓
Validate Destination
   ↓
Extract Source Schema
   ↓
Generate Target DDL
   ↓
Apply Schema
   ↓
Migration Complete
```

### Stage 1 — Initialize Migration

- **Batch wrapper:** `scripts/batch/migration/windows/initialize_migration.bat`
- **Python orchestration:** `scripts/python/migration/initialize.py`
- **Purpose:** Resolve effective SOURCE and DESTINATION configurations, validate database types, and confirm the source and destination are not identical endpoints.

### Stage 2 — Validate Source

- **Batch wrapper:** `scripts/batch/migration/windows/validate_source.bat`
- **Python orchestration:** `scripts/python/migration/validate_source.py`
- **Purpose:** Establish a connection to the source database, verify the database is reachable, and confirm the configured schema exists.

### Stage 3 — Validate Destination

- **Batch wrapper:** `scripts/batch/migration/windows/validate_destination.bat`
- **Python orchestration:** `scripts/python/migration/validate_destination.py`
- **Purpose:** Determine whether the destination database exists. If missing, create it automatically, then reconnect and validate the connection and schema.

### Stage 4 — Extract Source Schema

- **Batch wrapper:** `scripts/batch/migration/windows/extract_schema.bat`
- **Python orchestration:** `scripts/python/migration/extract_schema.py`
- **Purpose:** Invoke the schema extractor for the target database type and write extracted table/column metadata to `metadata/<database>/`.

### Stage 5 — Generate Target DDL

- **Batch wrapper:** `scripts/batch/migration/windows/generate_ddl.bat`
- **Python orchestration:** `scripts/python/migration/generate_ddl.py`
- **Purpose:** Read `metadata/<database>/schema_registry.json`, generate Liquibase XML changelogs into `liquibase/migration/<database>/`, and update `master.xml`.

### Stage 6 — Apply Schema

- **Batch wrapper:** `scripts/batch/migration/windows/apply_schema.bat`
- **Python orchestration:** `scripts/python/migration/apply_schema.py`
- **Purpose:** Execute Liquibase `update` against the destination database using the migration-specific changelog and runner.

---

## Implementation Locations

| Layer | Path |
|-------|------|
| Batch wrappers | `scripts/batch/migration/windows/` |
| Python orchestration | `scripts/python/migration/` |
| Migration configuration | `config/windows/migration/` |
| Migration Liquibase output | `liquibase/migration/<database>/` |
| Extracted metadata | `metadata/<database>/` |
| Jenkins pipeline | `migration/windows/Jenkinsfile` |

---

## Configuration Resolution

### Source Resolution

```
source.conf
   ↓
SOURCE_DATABASE
   ↓
selected database config:
mssql.conf / mysql.conf / postgresql.conf
```

### Destination Resolution

```
destination.conf
   ↓
DESTINATION_DATABASE
   ↓
selected database config:
mssql.conf / mysql.conf / postgresql.conf
```

### Precedence (highest to lowest)

1. **Non-empty Jenkins/runtime environment override** (`SOURCE_*` / `DESTINATION_*`)
2. **Role-level migration config** (`source.conf` / `destination.conf`)
3. **Database-specific migration config** (`mssql.conf` / `mysql.conf` / `postgresql.conf`)

> Empty Jenkins parameters do **NOT** override configured defaults. Only non-empty values take precedence.

### Example

```
SOURCE_DATABASE=MSSQL
→ config/windows/migration/mssql.conf

DESTINATION_DATABASE=POSTGRESQL
→ config/windows/migration/postgresql.conf
```

SOURCE and DESTINATION may use different database types.

---

## Liquibase Isolation

| Environment | Directory |
|-------------|-----------|
| Production | `liquibase/mysql/`<br>`liquibase/mssql/`<br>`liquibase/postgresql/` |
| Migration | `liquibase/migration/mysql/`<br>`liquibase/migration/mssql/`<br>`liquibase/migration/postgresql/` |

Migration generation and application must **not** use production Liquibase directories as temporary output.
