# Failure Points and Troubleshooting

## What This Covers

Known failure points in the migration pipeline, their symptoms, likely causes, and how to diagnose/resolve them.

## Stage-Level Failure Map

| Stage | Common Failure | Likely Cause | Resolution |
|-------|---------------|--------------|------------|
| 1. Initialize | `Configuration file not found` | Config file missing or wrong path | Verify `config/windows/migration/` exists |
| 1. Initialize | `Unsupported DATABASE type` | Invalid `SOURCE_DATABASE`/`DESTINATION_DATABASE` value | Use `MSSQL`, `MYSQL`, or `POSTGRESQL` |
| 1. Initialize | `Missing required fields` | Config file missing HOST, PORT, DB, or USER | Check database-specific config file |
| 1. Initialize | `Source and destination resolve to the exact same database` | Same type, host, port, and database name | Change source or destination to a different endpoint |
| 2. Validate Source | `Connection refused` | Source DB not running or wrong host/port | Start DB, verify `sqlcmd`/`mysql`/`psql` connectivity |
| 2. Validate Source | `ODBC driver not found` | MSSQL ODBC driver missing | Install MSSQL ODBC Driver 17 |
| 3. Validate Destination | `Connection refused` | Destination DB not running | Start destination DB server |
| 3. Validate Destination | `Permission denied` | User lacks `CREATE DATABASE` privilege | Grant `CREATE` (MySQL) / `CREATEDB` (PostgreSQL) / `CREATE DATABASE` (MSSQL) |
| 4. Extract Schema | `Schema extractor not found` | `scripts/schema_extractor.py` missing | Verify file exists at project root |
| 4. Extract Schema | `No columns found for table` | Source table is empty or permissions issue | Check source table data and user permissions |
| 5. Generate DDL | `Schema registry not found` | Stage 4 did not run or wrote to wrong path | Verify `metadata/<database>/schema_registry.json` exists |
| 5. Generate DDL | `No schema changes detected` | Normal idempotent behavior, not an error | This is expected when schema is unchanged |
| 6. Install Liquibase | `Liquibase installation failed` | Network/download issue | Verify network access, retry |
| 7. Install Drivers | `Driver installation failed` | Network/download issue | Verify network access, retry |
| 8. Apply Schema | `Liquibase validation failed` | Liquibase version mismatch | Verify `LIQUIBASE_VERSION` in config |
| 8. Apply Schema | `JDBC driver not found` | Driver missing from `tools/drivers/` | Run Install Drivers stage first |
| 8. Apply Schema | `Changelog not found` | Wrong changelog path | Verify `liquibase/migration/<db>/master.xml` exists |
| 8. Apply Schema | `Checksum mismatch` | Stale `DATABASECHANGELOG` entries | Clean test database, use isolated migration directory |
| 8. Apply Schema | `Connection failed` | Destination DB down or wrong credentials | Verify DB server and credentials |

## Database-Specific Troubleshooting

### MSSQL Source Connection

```sql
-- Verify server is running
sqlcmd -S localhost,1533 -U sa -P 'Password@123' -Q "SELECT 1"

-- Verify database exists
sqlcmd -S localhost,1533 -U sa -P 'Password@123' -d ecommerce_mssql -Q "SELECT name FROM sys.tables"

-- Verify schema exists
sqlcmd -S localhost,1533 -U sa -P 'Password@123' -d ecommerce_mssql -Q "SELECT name FROM sys.schemas WHERE name = 'dbo'"
```

### MySQL Destination Connection

```sql
-- Verify server is running
mysql -u rootuser -p -h 127.0.0.1 -P 3306 -e "SHOW DATABASES;"

-- Verify database exists
mysql -u rootuser -p -h 127.0.0.1 -P 3306 -e "USE test_schema_1; SHOW TABLES;"
```

## Configuration Debugging

### Check Effective Configuration

The `Initialize Migration` stage prints the effective configuration. Compare it against expected values:

```
Database : MSSQL          ← Should match SOURCE_DATABASE
Host     : localhost      ← Should match SOURCE_HOST or mssql.conf
Port     : 1533           ← Should match SOURCE_PORT or mssql.conf
DB       : ecommerce_mssql ← Should match SOURCE_DB or mssql.conf
```

### Verify Config File Contents

```cmd
REM Windows
type config\windows\migration\source.conf
type config\windows\migration\destination.conf
type config\windows\migration\mssql.conf
type config\windows\migration\mysql.conf
```

### Verify Config Loader Behavior

Run Python directly:
```cmd
python scripts\python\migration\initialize.py
```

This bypasses the batch wrapper and shows raw Python output.

## Liquibase Troubleshooting

### Verify Liquibase Installation

```cmd
C:\Users\Admin\.jenkins\workspace\001_mig_shema_extrat\tools\liquibase\liquibase.bat --version
```

### Check Changelog Path

```cmd
dir liquibase\migration\mysql\
type liquibase\migration\mysql\master.xml
```

### Check DATABASECHANGELOG

```sql
-- MySQL
SELECT * FROM DATABASECHANGELOG;

-- PostgreSQL
SELECT * FROM DATABASECHANGELOG;

-- MSSQL
SELECT * FROM DATABASECHANGELOG;
```

### Checksum Mismatch Resolution

If you encounter checksum errors:
1. Drop the test database and let the pipeline recreate it, OR
2. Clear `DATABASECHANGELOG` table manually, OR
3. Use a fresh test database name via Jenkins parameter override

## Common Error Patterns

| Error Message | Layer | Fix |
|--------------|-------|-----|
| `source.conf.conf not found` | Configuration | Use `load_migration_role_config("source")`, not `load_migration_config("source.conf")` |
| `MYSQL.conf not found` (Linux) | Configuration | Normalize DB type to lowercase before path construction |
| `NameError: load_migration_role_config` | Python | Add missing import from `config_loader.py` |
| `Permission denied` / exit 126 | Linux/Jenkins | `chmod +x` scripts, ensure single `checkout scm` |
| `echo.: command not found` / exit 127 | Linux Shell | Replace Windows `echo.` with Linux `echo` |
| `Connection refused` | Database | Start DB server, check port, verify firewall |
| `Driver not found` | Liquibase | Run Install Drivers stage, verify `tools/drivers/` path |
| `master.xml not found` | Liquibase | Verify path points to `liquibase/migration/<db>/` |

## Safe Debugging Rules

1. **Do not modify unrelated layers.** If the error is in configuration, do not change Python code.
2. **Reproduce locally if possible.** Run the failing Python module directly from the command line.
3. **Fix the smallest responsible layer.** A shell script syntax error should be fixed in the shell script, not in Python.
4. **Run syntax validation before testing.**
   - Windows: `cmd /c script.bat`
   - Linux: `bash -n script.sh`
5. **Run local test** after fix.
6. **Run Jenkins** to verify pipeline integration.
7. **Verify output database** after successful migration.

## Verification Checklist

After a successful migration, verify:
- [ ] Stage 1 shows PASS with correct source/destination summary
- [ ] Stage 2 confirms source connection and schema
- [ ] Stage 3 confirms destination connection (auto-created if missing)
- [ ] Stage 4 created `metadata/<database>/schema_registry.json`
- [ ] Stage 5 generated `liquibase/migration/<database>/*.xml` and updated `master.xml`
- [ ] Stage 6 Liquibase update completed without errors
- [ ] Destination database contains expected tables
- [ ] No production Liquibase directories were modified
