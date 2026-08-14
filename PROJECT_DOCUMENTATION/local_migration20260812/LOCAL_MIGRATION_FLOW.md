# Local Migration Pipeline Flow

## Overview

This document describes the local database migration pipeline, which extracts schema from a source database, generates Liquibase DDL, and applies it to a destination database. The pipeline supports both Windows and Linux environments.

## Pipeline Architecture

```
              Jenkins Parameters
                     |
                     v
           Source / Destination
              Configuration
                     |
                     v
           Common Python Layer
                     |
           +---------+---------+
           |                   |
        Windows             Linux
           |                   |
        .bat               .sh
           |                   |
           +---------+---------+
                     |
                     v
           Migration Engine
                     |
           +---------+---------+
           |         |         |
        Extract   Generate   Apply
        Schema      DDL     Liquibase
                     |
                     v
           liquibase/migration/
                     |
                     v
           Destination Database
```

## Six Core Migration Stages

### Stage 1 — Initialize Migration

- **Batch wrapper:** `scripts/batch/migration/windows/initialize_migration.bat`
- **Shell wrapper:** `scripts/bash/migration/linux/initialize_migration.sh`
- **Python orchestration:** `scripts/python/migration/initialize.py`
- **Purpose:** Resolve effective SOURCE and DESTINATION configurations, validate database types, and confirm the source and destination are not identical endpoints.

### Stage 2 — Validate Source

- **Batch wrapper:** `scripts/batch/migration/windows/validate_source.bat`
- **Shell wrapper:** `scripts/bash/migration/linux/validate_source.sh`
- **Python orchestration:** `scripts/python/migration/validate_source.py`
- **Purpose:** Establish a connection to the source database, verify the database is reachable, and confirm the configured schema exists.

### Stage 3 — Validate Destination

- **Batch wrapper:** `scripts/batch/migration/windows/validate_destination.bat`
- **Shell wrapper:** `scripts/bash/migration/linux/validate_destination.sh`
- **Python orchestration:** `scripts/python/migration/validate_destination.py`
- **Purpose:** Determine whether the destination database exists. If missing, create it automatically, then reconnect and validate the connection and schema.

### Stage 4 — Extract Source Schema

- **Batch wrapper:** `scripts/batch/migration/windows/extract_schema.bat`
- **Shell wrapper:** `scripts/bash/migration/linux/extract_schema.sh`
- **Python orchestration:** `scripts/python/migration/extract_schema.py`
- **Purpose:** Invoke the schema extractor for the target database type and write extracted table/column metadata to `metadata/<database>/`.

### Stage 5 — Generate Target DDL

- **Batch wrapper:** `scripts/batch/migration/windows/generate_ddl.bat`
- **Shell wrapper:** `scripts/bash/migration/linux/generate_ddl.sh`
- **Python orchestration:** `scripts/python/migration/generate_ddl.py`
- **Purpose:** Read `metadata/<database>/schema_registry.json`, generate Liquibase XML changelogs into `liquibase/migration/<database>/`, and update `master.xml`.

### Stage 6 — Apply Schema

- **Batch wrapper:** `scripts/batch/migration/windows/apply_schema.bat`
- **Shell wrapper:** `scripts/bash/migration/linux/apply_schema.sh`
- **Python orchestration:** `scripts/python/migration/apply_schema.py`
- **Purpose:** Execute Liquibase `update` against the destination database using the migration-specific changelog and runner.

---

## Linux Supporting Stages

On Linux, Jenkins executes two additional stages before Stage 6 (Apply Schema) to prepare the runtime environment. These are platform/runtime preparation stages, not separate migration business logic.

### Set Permissions

```bash
find scripts/bash -type f -name "*.sh" -exec chmod +x {} \;
```

This stage ensures all `.sh` scripts are executable after the Jenkins checkout.

### Install Liquibase

```bash
scripts/bash/common/install_liquibase.sh
```

Installs the Liquibase runtime required for Stage 6.

### Install Drivers

```bash
scripts/bash/mysql/setup/install_mysql_driver.sh
scripts/bash/postgresql/setup/install_postgresql_driver.sh
scripts/bash/common/install_mssql_driver.sh
```

Installs JDBC drivers for all supported databases. Required for Stage 6 to connect to the destination.

---

## Windows vs Linux Comparison

| Layer | Windows | Linux | Shared? |
|-------|---------|-------|---------|
| Jenkins pipeline | `migration/windows/Jenkinsfile` | `migration/linux/Jenkinsfile` | No |
| Script wrappers | `scripts/batch/migration/windows/*.bat` | `scripts/bash/migration/linux/*.sh` | No |
| Python orchestration | `scripts/python/migration/*.py` | `scripts/python/migration/*.py` | **Yes** |
| Configuration | `config/windows/migration/` | `config/linux/migration/` | No (platform-specific) |
| Liquibase output | `liquibase/migration/<database>/` | `liquibase/migration/<database>/` | **Yes** |
| Metadata output | `metadata/<database>/` | `metadata/<database>/` | **Yes** |

**Key points:**

- **Python migration modules are shared** between Windows and Linux.
- **Platform-specific wrappers** (`.bat` vs `.sh`) are different.
- **Configuration is platform-specific** and resolved through `config_loader.py`.
- **Jenkins execution is platform-specific** (separate Jenkinsfiles).
- **Business migration flow remains the same** across both platforms.

---

## Python Architecture

### Shared Migration Modules

All Python modules in `scripts/python/migration/` are shared by both Windows and Linux. The platform wrappers invoke these modules; the modules themselves do not contain OS-specific logic.

| Module | Responsibility |
|--------|---------------|
| `initialize.py` | Resolves effective source/destination config, validates database types, prevents same-endpoint migration |
| `validate_source.py` | Tests source connection and validates schema existence |
| `validate_destination.py` | Tests destination connection, auto-creates missing database, validates schema |
| `extract_schema.py` | Invokes database-specific schema extractors and writes metadata |
| `generate_ddl.py` | Reads `schema_registry.json`, generates Liquibase XML into `liquibase/migration/<db>/` |
| `apply_schema.py` | Invokes Liquibase runner to apply changelog to destination |

### Configuration Loader

`scripts/python/common/config_loader.py` is responsible for resolving platform-specific paths:

```python
def get_migration_config_path(name):
    if platform.system() == "Windows":
        return ROOT / "config" / "windows" / "migration" / f"{name}.conf"
    else:
        return ROOT / "config" / "linux" / "migration" / f"{name}.conf"

def load_migration_config(database_name):
    return load_config(get_migration_config_path(database_name))

def load_migration_role_config(role):
    return load_config(get_migration_config_path(role))
```

Migration Python modules do **not** call `platform.system()` directly for config path resolution. OS-specific path selection is centralized in `config_loader.py`.

### Important: Migration Config vs Production Config

- **Migration config:** `config/linux/migration/` and `config/windows/migration/`
- **Production database config:** `config/ubuntu/` (Linux production setup)

These are separate directories. Do not confuse migration testing configuration with production database configuration.

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
  or
→ config/linux/migration/mssql.conf

DESTINATION_DATABASE=MYSQL
→ config/windows/migration/mysql.conf
  or
→ config/linux/migration/mysql.conf
```

SOURCE and DESTINATION may use different database types.

---

## Liquibase Isolation

| Environment | Directory |
|-------------|-----------|
| Production | `liquibase/mysql/`<br>`liquibase/mssql/`<br>`liquibase/postgresql/` |
| Migration | `liquibase/migration/mysql/`<br>`liquibase/migration/mssql/`<br>`liquibase/migration/postgresql/` |

Migration generation and application must **not** use production Liquibase directories as temporary output.

### Stage 5 (Generate DDL)

```
schema_registry.json
      ↓
migration DDL generator
      ↓
liquibase/migration/<destination_db>/
```

### Stage 6 (Apply Schema)

```
liquibase/migration/<destination_db>/master.xml
      ↓
Liquibase
      ↓
destination database
```

This isolation was introduced because earlier testing modified/reused production Liquibase changelogs and caused checksum problems.

---

## Linux-Specific Behavior

### 1. Executable Permissions

After Jenkins checkout, the **Set Permissions** stage runs:

```bash
find scripts/bash -type f -name "*.sh" -exec chmod +x {} \;
```

This ensures all `.sh` scripts can be executed. Without this, Jenkins on Linux will fail with `Permission denied` (exit code 126).

### 2. Duplicate Checkout Problem

The following sequence causes failures:

```
Set Permissions
   ↓
chmod +x
   ↓
checkout scm again
   ↓
permissions reset
   ↓
Permission denied / exit code 126
```

**Rule:** Declarative Jenkins checkout occurs once, in the Initialize Migration stage. No later stage should call `checkout scm` again.

### 3. Linux Case Sensitivity

Linux filesystem paths are case-sensitive.

```
Jenkins parameter:     MYSQL
Linux config file:     mysql.conf

Incorrect: config/linux/migration/MYSQL.conf
Correct:   config/linux/migration/mysql.conf
```

Current normalization in scripts:

```bash
${DB_TYPE,,}
```

Mapping:
- `MYSQL` → `mysql`
- `MSSQL` → `mssql`
- `POSTGRESQL` → `postgresql`

This normalization is required because Linux filesystem paths are case-sensitive.

### 4. Linux Shell Syntax

Linux migration scripts must not contain Windows-only commands:

| Windows (Incorrect) | Linux (Correct) |
|---------------------|-----------------|
| `echo.` | `echo` or `printf '\n'` |
| `call script.bat` | `./script.sh` |
| `if errorlevel 1` | `if [ $? -ne 0 ]` |
| `.bat paths` | `.sh paths` |
| `%VARIABLE%` | `$VARIABLE` |

---

## Implementation Locations

| Layer | Windows | Linux |
|-------|---------|-------|
| Jenkins pipeline | `migration/windows/Jenkinsfile` | `migration/linux/Jenkinsfile` |
| Batch wrappers | `scripts/batch/migration/windows/` | N/A |
| Shell wrappers | N/A | `scripts/bash/migration/linux/` |
| Python orchestration | `scripts/python/migration/` | `scripts/python/migration/` |
| Migration configuration | `config/windows/migration/` | `config/linux/migration/` |
| Migration Liquibase output | `liquibase/migration/<database>/` | `liquibase/migration/<database>/` |
| Extracted metadata | `metadata/<database>/` | `metadata/<database>/` |
