# Configuration and Parameter Resolution

## What This Covers

How Jenkins parameters, configuration files, and runtime environment variables combine to produce the effective source and destination configuration used by every migration stage.

## Configuration File Hierarchy

### Source Configuration

```
source.conf  (role-level defaults)
    ↓ provides defaults
mssql.conf / mysql.conf / postgresql.conf  (database-specific defaults)
    ↓ provides defaults
Jenkins Parameters (runtime overrides, if non-empty)
    ↓
Effective SOURCE Configuration
```

### Destination Configuration

```
destination.conf  (role-level defaults)
    ↓ provides defaults
mssql.conf / mysql.conf / postgresql.conf  (database-specific defaults)
    ↓ provides defaults
Jenkins Parameters (runtime overrides, if non-empty)
    ↓
Effective DESTINATION Configuration
```

## Precedence (Highest to Lowest)

| Priority | Source | Example |
|----------|--------|---------|
| 1 | Non-empty Jenkins / runtime environment override | `SOURCE_HOST=10.0.0.1` |
| 2 | Role-level migration config | `config/windows/migration/source.conf` |
| 3 | Database-specific migration config | `config/windows/migration/mssql.conf` |

**Critical rule:** Empty Jenkins parameters do NOT override configuration defaults. Only non-empty values take precedence. This is enforced in `initialize.py` via the `env_override()` function.

## Configuration Files

### source.conf

```properties
SOURCE_DATABASE=MSSQL
SOURCE_SCHEMA=dbo
```

This file defines the **source role defaults**. Only `SOURCE_DATABASE` and `SOURCE_SCHEMA` are set here. All other source fields (HOST, PORT, DB, USER, PASSWORD) are inherited from the selected database config file.

### destination.conf

```properties
DESTINATION_DATABASE=MYSQL
DESTINATION_SCHEMA=
```

This file defines the **destination role defaults**. Only `DESTINATION_DATABASE` and `DESTINATION_SCHEMA` are set here. All other destination fields are inherited from the selected database config file.

### mssql.conf

```properties
MSSQL_HOST=localhost
MSSQL_PORT=1533
MSSQL_DB=ecommerce_mssql
MSSQL_USER=sa
MSSQL_PASSWORD=Password@123
MSSQL_INSTANCE=DMSQL
MSSQL_DRIVER_VERSION=12.10.0
MSSQL_ODBC_DRIVER=ODBC Driver 17 for SQL Server
LIQUIBASE_VERSION=5.0.3
```

### mysql.conf

```properties
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_DB=ecommerce_mysql
MYSQL_USER=rootuser
MYSQL_PASSWORD=root123
MYSQL_VERSION=9.7.0
MYSQL_DRIVER_VERSION=9.5.0
LIQUIBASE_VERSION=5.0.3
```

### postgresql.conf

```properties
POSTGRESQL_HOST=127.0.0.1
POSTGRESQL_PORT=55432
POSTGRESQL_DB=ecommerce_postgresql
POSTGRESQL_USER=postgres
POSTGRESQL_PASSWORD=root1234
POSTGRESQL_VERSION=17
POSTGRESQL_DRIVER_VERSION=42.7.3
LIQUIBASE_VERSION=5.0.3
```

## How Resolution Works

### Step 1 — Load Database Defaults

All three database config files are loaded and merged into a single dictionary:

```python
db_defaults = {}
for db_name in ["mssql", "mysql", "postgresql"]:
    db_defaults.update(load_migration_config(db_name))
```

This produces a flat dictionary like:
```
{
    "MSSQL_HOST": "localhost",
    "MSSQL_PORT": "1533",
    ...
    "MYSQL_HOST": "127.0.0.1",
    ...
}
```

### Step 2 — Map Database Defaults to Role Keys

The `map_db_config_to_role()` function selects only the keys relevant to the selected database type and maps them to the role prefix:

```python
# For SOURCE_DATABASE=MSSQL:
# MSSQL_HOST → SOURCE_HOST
# MSSQL_PORT → SOURCE_PORT
# MSSQL_DB   → SOURCE_DB
```

### Step 3 — Apply Role Defaults

Role-level defaults from `source.conf` or `destination.conf` are applied on top of mapped database defaults.

### Step 4 — Apply Environment Overrides

`env_override()` checks all environment variables that start with the role prefix (`SOURCE_` or `DESTINATION_`). Non-empty values override the effective config.

### Step 5 — Validate

The resulting effective config is validated for required fields and same-endpoint check.

## Required Fields per Role

```python
required = [
    f"{role}_DATABASE",
    f"{role}_HOST",
    f"{role}_PORT",
    f"{role}_DB",
    f"{role}_USER",
]
```

`PASSWORD` is used but not listed as strictly required in the code (connection will fail if missing, but validation does not explicitly check it).

## Example Resolution

Given:
- Jenkins parameter: `SOURCE_DATABASE=MSSQL`
- `source.conf`: `SOURCE_DATABASE=MSSQL`, `SOURCE_SCHEMA=dbo`
- `mssql.conf`: `MSSQL_HOST=localhost`, `MSSQL_PORT=1533`, `MSSQL_DB=ecommerce_mssql`, `MSSQL_USER=sa`, `MSSQL_PASSWORD=Password@123`

Effective SOURCE config:
```
SOURCE_DATABASE = MSSQL      (from source.conf / Jenkins)
SOURCE_HOST     = localhost  (from mssql.conf)
SOURCE_PORT     = 1533       (from mssql.conf)
SOURCE_DB       = ecommerce_mssql  (from mssql.conf)
SOURCE_SCHEMA   = dbo         (from source.conf)
SOURCE_USER     = sa          (from mssql.conf)
SOURCE_PASSWORD = Password@123 (from mssql.conf)
```

If Jenkins provides `SOURCE_PORT=1534`, the effective config becomes:
```
SOURCE_PORT = 1534  (overridden by Jenkins)
```

If Jenkins provides `SOURCE_PORT=` (empty), the effective config remains:
```
SOURCE_PORT = 1533  (from mssql.conf, NOT overridden)
```

## Configuration File Locations

| Config | Windows Path |
|--------|-------------|
| Source role config | `config/windows/migration/source.conf` |
| Destination role config | `config/windows/migration/destination.conf` |
| MSSQL database config | `config/windows/migration/mssql.conf` |
| MySQL database config | `config/windows/migration/mysql.conf` |
| PostgreSQL database config | `config/windows/migration/postgresql.conf` |

## Linux Configuration Paths

| Config | Linux Path |
|--------|------------|
| Source role config | `config/linux/migration/source.conf` |
| Destination role config | `config/linux/migration/destination.conf` |
| Database configs | `config/linux/migration/<db>.conf` |

**Note:** Linux path resolution requires lowercase database names (`mysql.conf`, not `MYSQL.conf`). The `config_loader.py` handles this via `platform.system()` branching.
