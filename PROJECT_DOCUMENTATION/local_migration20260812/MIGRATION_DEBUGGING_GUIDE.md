# Migration Debugging Guide

Practical reference for debugging the local migration pipeline on Windows and Linux.

---

## 1. Pipeline Architecture

```
Jenkins Parameters
   |
   v
Source / Destination Configuration
   |
   v
Common Python Layer
   |
   +---------+---------+
   |                   |
Windows              Linux
   |                   |
.bat                 .sh
   |                   |
   +---------+---------+
             |
             v
      Migration Engine
             |
   +---------+---------+
   |         |         |
Extract   Generate   Apply
Schema     DDL     Liquibase
             |
             v
      liquibase/migration/
             |
             v
      Destination Database
```

---

## 2. Stage-to-File Mapping

| Stage | Main Python | Windows Wrapper | Linux Wrapper | Typical Failure | First Check |
|-------|-------------|-----------------|---------------|-----------------|-------------|
| Initialize | `initialize.py` | `initialize_migration.bat` | `initialize_migration.sh` | Configuration | Check effective source/destination values |
| Validate Source | `validate_source.py` | `validate_source.bat` | `validate_source.sh` | Connection / schema | Check source DB connectivity |
| Validate Destination | `validate_destination.py` | `validate_destination.bat` | `validate_destination.sh` | Connection / database missing | Check bootstrap + auto-create |
| Extract Schema | `extract_schema.py` | `extract_schema.bat` | `extract_schema.sh` | Driver / query / schema | Check metadata output |
| Generate DDL | `generate_ddl.py` | `generate_ddl.bat` | `generate_ddl.sh` | Missing registry / invalid schema | Check `liquibase/migration/<db>` |
| Apply Schema | `apply_schema.py` + Liquibase runner | `apply_schema.bat` / `run_liquibase.bat` | `apply_schema.sh` / `run_liquibase.sh` | Liquibase / driver / checksum | Check changelog + DATABASECHANGELOG |

---

## 3. Configuration Debugging

### Effective config resolution

```
Jenkins params (non-empty)
   ↓ overrides
source.conf / destination.conf
   ↓ provides defaults
mssql.conf / mysql.conf / postgresql.conf
```

### Check effective values

```bash
# Windows
type config\windows\migration\source.conf
type config\windows\migration\destination.conf
type config\windows\migration\mysql.conf

# Linux
cat config/linux/migration/source.conf
cat config/linux/migration/destination.conf
cat config/linux/migration/mysql.conf
```

### Verify normalization (Linux)

```bash
# Uppercase Jenkins parameter must resolve to lowercase config
echo ${DB_TYPE,,}    # should print: mysql / mssql / postgresql
```

### Common config errors

| Symptom | Likely Cause |
|---------|-------------|
| `source.conf.conf` not found | Used `load_migration_config("source.conf")` instead of `load_migration_role_config("source")` |
| `MYSQL.conf` not found (Linux) | Case-sensitive path — need `${DB_TYPE,,}` normalization |
| Missing required fields | `source.conf` or `database.conf` missing a required key |
| Same source and destination | `SOURCE_DATABASE`, `SOURCE_HOST`, `SOURCE_PORT`, `SOURCE_DB` all match destination |

---

## 4. Windows Debugging

### Verify script syntax

```cmd
cmd /c scripts\batch\migration\windows\initialize_migration.bat
```

### Check Python output

```cmd
python scripts\python\migration\initialize.py
```

### Common Windows errors

| Error | Cause | Fix |
|-------|-------|-----|
| `python` not recognized | Python not in PATH | Use full path or fix PATH |
| `FileNotFoundError` for `.conf` | Wrong config path | Verify `config/windows/migration/` exists |
| ODBC driver not found | MSSQL driver missing | Install MSSQL ODBC driver |

---

## 5. Linux Debugging

### Verify shell syntax

```bash
bash -n scripts/bash/migration/linux/*.sh
```

### Check permissions

```bash
find scripts/bash/migration/linux -type f -name "*.sh" -exec ls -l {} \;
```

### Common Linux errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Permission denied` (exit 126) | Scripts not executable | `chmod +x` or check for duplicate `checkout scm` |
| `command not found` (exit 127) | Windows syntax in `.sh` | Replace `echo.` with `echo`, etc. |
| `MYSQL.conf` not found | Case-sensitive path | Normalize with `${DB_TYPE,,}` |
| `python3: not found` | Python3 not installed | Install Python 3 |

---

## 6. Database Connection Debugging

### MySQL

```sql
-- Check server running
mysql -u root -p -e "SHOW DATABASES;"

-- Check specific database
mysql -u <user> -p -e "USE <db>; SHOW TABLES;"
```

### PostgreSQL

```sql
-- List databases
psql -U postgres -c "\l"

-- Connect to specific database
psql -U <user> -d <db> -c "\dt"
```

### MSSQL

```sql
-- List databases
sqlcmd -S localhost -U sa -P '<password>' -Q "SELECT name FROM sys.databases;"

-- Connect to specific database
sqlcmd -S localhost -U sa -P '<password>' -d <db> -Q "SELECT name FROM sys.tables;"
```

### Connection checklist

1. Is the database server running?
2. Can you connect with the same credentials from the command line?
3. Is the port correct?
4. Is the user authorized from the connecting host?
5. Is the database name spelled correctly?

---

## 7. Database Auto-Create Debugging

### Verify auto-create behavior

```bash
# Run validate destination and watch for "does not exist" / "created successfully"
python scripts/python/migration/validate_destination.py
```

### Database-specific notes

| Database | Bootstrap DB | Auto-create works if |
|----------|-------------|---------------------|
| MySQL | None (server-level) | User has `CREATE` privilege |
| PostgreSQL | `postgres` | User has `CREATEDB` privilege or is superuser |
| MSSQL | `master` | User has `CREATE DATABASE` permission |

### Verify database was created

```sql
-- MySQL
SHOW DATABASES;

-- PostgreSQL
\l

-- MSSQL
SELECT name FROM sys.databases;
```

---

## 8. Schema Extraction Debugging

### Check metadata output

```bash
# Windows
dir metadata\<database>\

# Linux
ls -la metadata/<database>/
```

### Verify schema_registry.json

```bash
# Windows
type metadata\<database>\schema_registry.json

# Linux
cat metadata/<database>/schema_registry.json
```

### Common extraction errors

| Symptom | Likely Cause |
|---------|-------------|
| Empty `schema_registry.json` | Source schema is empty or extractor query failed |
| Missing tables | Source schema name mismatch |
| Permission denied on metadata write | Directory does not exist or lacks write permissions |

---

## 9. DDL Generation Debugging

### Check generated files

```bash
# Windows
dir liquibase\migration\<database>\

# Linux
ls -la liquibase/migration/<database>/
```

### Verify master.xml

```bash
# Windows
type liquibase\migration\<database>\master.xml

# Linux
cat liquibase/migration/<database>/master.xml
```

### Common generation errors

| Symptom | Likely Cause |
|---------|-------------|
| `schema_registry.json` not found | Schema extraction did not run or wrote to wrong path |
| Empty `master.xml` | No schema changes detected |
| Duplicate changeset IDs | Previous generation artifacts not cleaned |

---

## 10. Liquibase Debugging

### Verify Liquibase installation

```bash
# Linux
liquibase --version

# Windows
liquibase.bat --version
```

### Check changelog path

```bash
# Should point to migration directory, NOT production
ls -la liquibase/migration/<database>/master.xml
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

### Common Liquibase errors

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| Checksum mismatch | Stale `DATABASECHANGELOG` entries | Clean test DB or use isolated migration directory |
| Driver not found | JDBC driver missing | Run Install Drivers stage |
| `master.xml` not found | Wrong changelog path | Verify path points to `liquibase/migration/<db>/` |
| Connection failed | Destination DB down | Check DB server and credentials |

---

## 11. Permission / Shell Debugging

### Linux permission fix

```bash
find scripts/bash -type f -name "*.sh" -exec chmod +x {} \;
```

### Verify no duplicate checkout

Check Jenkinsfile — `checkout scm` should appear only once, before Set Permissions.

### Verify shell syntax

```bash
bash -n scripts/bash/migration/linux/*.sh
bash -n scripts/bash/common/*.sh
```

---

## 12. Common Errors

| Error | Platform | Layer | Fix |
|-------|----------|-------|-----|
| `Permission denied` / exit 126 | Linux | Jenkins / Permissions | `chmod +x` + single checkout |
| `echo.: command not found` / exit 127 | Linux | Shell script | Replace Windows syntax |
| `source.conf.conf` not found | Both | Configuration | Use `load_migration_role_config("source")` |
| `MYSQL.conf` not found | Linux | Configuration | Normalize DB type to lowercase |
| `NameError: load_migration_role_config` | Both | Python | Add missing import |
| Connection refused | Both | Database | Start DB server, check port |
| Checksum mismatch | Both | Liquibase | Use isolated migration directory |
| Driver not found | Both | Liquibase | Install JDBC drivers |

---

## 13. Safe Debugging Rules

1. **Do not modify unrelated layers.** If the error is in configuration, do not change Python code.
2. **Reproduce locally if possible.** Run the failing Python module directly from the command line.
3. **Fix the smallest responsible layer.** A shell script syntax error should be fixed in the shell script, not in Python.
4. **Run syntax validation before testing.**
   - Windows: `cmd /c script.bat`
   - Linux: `bash -n script.sh`
5. **Run local test** after fix.
6. **Run Jenkins** to verify pipeline integration.
7. **Verify output database** after successful migration.

---

## 14. Verification Checklist

After a successful migration, verify:

- [ ] Stage 1 shows PASS with correct source/destination summary
- [ ] Stage 2 confirms source connection and schema
- [ ] Stage 3 confirms destination connection (auto-created if missing)
- [ ] Stage 4 created `metadata/<database>/schema_registry.json`
- [ ] Stage 5 generated `liquibase/migration/<database>/*.xml` and updated `master.xml`
- [ ] Stage 6 Liquibase update completed without errors
- [ ] Destination database contains expected tables
- [ ] No production Liquibase directories were modified

### Quick database verification commands

```sql
-- MySQL
USE <db>;
SHOW TABLES;

-- PostgreSQL
\c <db>
\dt

-- MSSQL
USE <db>;
SELECT name FROM sys.tables;
```
