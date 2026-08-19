# Source and Destination Validation

## What This Covers

How the pipeline validates connectivity to both the source and destination databases, including auto-creation of missing destination databases.

## Stage 2: Validate Source

**Batch wrapper:** `scripts/batch/migration/windows/validate_source.bat`
**Python module:** `scripts/python/migration/validate_source.py`

### What It Does

1. Resolves effective source configuration using the same precedence rules as initialization.
2. Validates database type is one of: `MSSQL`, `MYSQL`, `POSTGRESQL`.
3. Validates all required fields are present (DATABASE, HOST, PORT, DB, USER).
4. Establishes a test connection to the source database.
5. Verifies the connected database matches the configured database name.
6. Verifies the configured schema exists (for databases that support schemas).

### Source Validation Steps

| Step | Action | Failure Behavior |
|------|--------|------------------|
| 1 | Load effective source config | `FileNotFoundError` if config missing |
| 2 | Validate database type | Exit if unsupported type |
| 3 | Validate required fields | Exit if HOST, PORT, DB, USER missing |
| 4 | Test connection (`SELECT 1`) | Exit if connection fails |
| 5 | Verify database name | Exit if connected to wrong database |
| 6 | Verify schema | Exit if schema missing (MSSQL/PostgreSQL); MySQL always passes |

### Database-Specific Schema Verification

| Database | Schema Query | Notes |
|----------|-------------|-------|
| MSSQL | `SELECT name FROM sys.schemas WHERE name = ?` | Checks `sys.schemas` |
| PostgreSQL | `SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s` | Checks `information_schema` |
| MySQL | Always returns `True` | MySQL schema concept differs; no schema-level check performed |

## Stage 3: Validate Destination

**Batch wrapper:** `scripts/batch/migration/windows/validate_destination.bat`
**Python module:** `scripts/python/migration/validate_destination.py`

### What It Does

1. Resolves effective destination configuration.
2. Checks whether the destination database exists using a bootstrap connection.
3. If the database does NOT exist: **auto-creates it**.
4. Reconnects to the destination database.
5. Verifies the connected database matches the configured database name.
6. Verifies the configured schema exists (if applicable).

### Destination Validation Steps

| Step | Action | Failure Behavior |
|------|--------|------------------|
| 1 | Load effective destination config | `FileNotFoundError` if config missing |
| 2 | Validate database type | Exit if unsupported type |
| 3 | Validate required fields | Exit if HOST, PORT, DB, USER missing |
| 4 | Check database existence | Bootstrap connection to server/system DB |
| 5 | Auto-create if missing | `CREATE DATABASE` with database-specific syntax |
| 6 | Reconnect to destination DB | Exit if connection fails after creation |
| 7 | Verify database name | Exit if connected to wrong database |
| 8 | Verify schema | Exit if schema missing (MSSQL/PostgreSQL); MySQL always passes |

## Database Auto-Creation

### Why Auto-Creation Exists

During early testing, missing destination databases caused pipeline failures. Auto-creation was added so the pipeline can proceed without manual DBA intervention.

### Auto-Creation Behavior by Database

| Database | Bootstrap Connection | Create Statement | Special Handling |
|----------|---------------------|------------------|------------------|
| **MySQL** | Connect to server **without** selecting the destination database | `CREATE DATABASE \`<db_name>\`` | `conn.commit()` after creation |
| **PostgreSQL** | Connect to the `postgres` database | `CREATE DATABASE "<db_name>"` | Requires autocommit (cannot run inside a transaction) |
| **MSSQL** | Connect to `master` database | `CREATE DATABASE [<db_name>]` | `conn.autocommit = True` before execution |

### Safety Guarantee

**The pipeline NEVER automatically DROPS an existing destination database.** It only creates missing databases. If a database already exists, it is left untouched.

### Database Existence Check

| Database | Check Method |
|----------|-------------|
| MySQL | `SHOW DATABASES` → scan for case-insensitive match |
| PostgreSQL | Connect to `postgres`, query `pg_database` |
| MSSQL | Connect to `master`, query `sys.databases` |

## Same-Endpoint Prevention

The `validate_not_same_endpoint()` function in `initialize.py` blocks migrations where source and destination resolve to the exact same endpoint:

```python
same_db = source.DATABASE == dest.DATABASE
same_host = source.HOST == dest.HOST
same_port = source.PORT == dest.PORT
same_dbname = source.DB == dest.DB

if same_db and same_host and same_port and same_dbname:
    return False, "Source and destination resolve to the exact same database endpoint"
```

This prevents accidental self-migration even if the database type differs but the connection details match.

## Validation Output Format

Both validation stages print a structured summary:

```
====================================
SOURCE VALIDATION
====================================

SOURCE VALIDATION
-----------------------------------------------
Database : MSSQL
Host     : localhost
Port     : 1533
DB       : ecommerce_mssql
Schema   : dbo
User     : sa
Password : ************

Connection: PASS
Database : PASS (verified: Ecommerce_MSSQL)
Schema   : PASS

SOURCE VALIDATION: PASS
```

Destination validation adds the auto-create message when applicable:

```
Database test_schema_1 does not exist
Creating database test_schema_1...
Database created successfully
```
