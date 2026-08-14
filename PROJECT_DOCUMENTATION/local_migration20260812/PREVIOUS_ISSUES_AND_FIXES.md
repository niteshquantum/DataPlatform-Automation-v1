# Previous Issues and Fixes — Migration Pipeline

This document records issues encountered during local migration testing, their diagnoses, and the fixes applied. It covers both Windows and Linux environments.

---

## Issue 1: MySQL Destination Connection Refused

**Problem:** The pipeline could not connect to the MySQL destination database.

**Symptoms:**
- Can't connect to MySQL server on 127.0.0.1:3306
- Stage 3 (Validate Destination) failed immediately

**Root Cause:** Destination MySQL instance or database was not available.

**Where It Happened:** Stage 3 — Validate Destination (both Windows and Linux)

**How It Was Diagnosed:** Reviewing Jenkins logs showed a connection refused error before any validation logic could run.

**Fix:** Destination validation was changed to support database auto-create:

```
check existence
→ bootstrap connection
→ create database
→ reconnect
→ validate
```

**Verification:** Pipeline successfully creates missing MySQL databases and continues.

**Prevention:** Always ensure the destination DB server is running. If the database itself is missing, the pipeline handles auto-creation.

---

## Issue 2: Liquibase Checksum Mismatch

**Problem:** Liquibase validation failed with checksum errors.

**Symptoms:**
```
Validation Failed:
changesets check sum
```

**Root Cause:** Old `DATABASECHANGELOG` entries from previous migration test runs stored checksums that no longer matched the changed migration XML files.

**Where It Happened:** Stage 6 — Apply Schema

**How It Was Diagnosed:** Liquibase output explicitly reported checksum mismatch. Comparing the changelog files confirmed they had been modified after the previous test run wrote entries to `DATABASECHANGELOG`.

**Fix:** Use isolated migration Liquibase changelog directories and clean test databases between runs.

**Verification:** New test runs using `liquibase/migration/<database>/` do not inherit stale checksums from production or previous test runs.

**Prevention:** Never reuse the same destination database across unrelated migration tests without clearing `DATABASECHANGELOG`.

---

## Issue 3: Production Liquibase Contamination

**Problem:** Migration temporarily wrote generated changelogs into production Liquibase directories.

**Symptoms:** Production Liquibase directories (`liquibase/mysql/`, `liquibase/mssql/`, `liquibase/postgresql/`) contained migration-generated files mixed with production changelogs.

**Root Cause:** Migration generation and application paths were not isolated from production Liquibase directories.

**Where It Happened:** Stage 5 — Generate DDL, and Stage 6 — Apply Schema

**How It Was Diagnosed:** Inspection of `liquibase/` directory showed migration-generated XML files alongside production changelogs.

**Fix:** Dedicated migration Liquibase directories were introduced:

```
liquibase/migration/mysql/
liquibase/migration/mssql/
liquibase/migration/postgresql/
```

Migration Stage 5 now generates directly into this isolated directory. Production Liquibase directories remain separate and untouched.

**Verification:** `liquibase/migration/<database>/` contains only migration-generated files. Production directories are unchanged.

**Prevention:** Never point migration generation or application to production Liquibase paths.

---

## Issue 4: source.conf.conf — Double Extension

**Problem:** Configuration loader received a filename with an extra `.conf` extension.

**Symptoms:**
```
config/windows/migration/source.conf.conf
```

**Root Cause:** `load_migration_config("source.conf")` was called, but `config_loader.py` automatically appends `.conf` to the provided name, resulting in `source.conf.conf`.

**Where It Happened:** Stage 1 — Initialize Migration

**How It Was Diagnosed:** Python traceback showed `FileNotFoundError` for `source.conf.conf`.

**Fix:** Use `load_migration_role_config("source")` instead of `load_migration_config("source.conf")`:

```python
# Incorrect
load_migration_config("source.conf")

# Correct
load_migration_role_config("source")
```

**Verification:** Configuration loads successfully with correct filename.

**Prevention:** Always pass bare role names (`source`, `destination`) to `load_migration_role_config()`. Only database names (`mysql`, `mssql`, `postgresql`) should be passed to `load_migration_config()`.

---

## Issue 5: load_migration_role_config Not Defined

**Problem:** `load_migration_role_config` was used but not imported.

**Symptoms:**
```
NameError: name 'load_migration_role_config' is not defined
```

**Root Cause:** The function was used in a Python module but not imported from `config_loader.py`.

**Where It Happened:** Stage 1 — Initialize Migration and downstream modules

**How It Was Diagnosed:** Python traceback showed `NameError` on `load_migration_role_config`.

**Fix:** Correct import from `config_loader.py`:

```python
from scripts.python.common.config_loader import (
    load_migration_config,
    load_migration_role_config,
)
```

**Verification:** Module imports successfully and configuration loads.

**Prevention:** When adding new migration Python modules, ensure all required imports from `config_loader.py` are included.

---

## Issue 6: Linux Permission Denied

**Problem:** Shell scripts could not execute on Linux Jenkins agents.

**Symptoms:**
```
initialize_migration.sh: Permission denied
exit code 126
```

**Root Cause:** Jenkins `checkout scm` resets file permissions. If `chmod +x` is followed by another `checkout scm`, executable permissions are lost.

**Where It Happened:** Linux Jenkins pipeline — Set Permissions stage

**How It Was Diagnosed:** Jenkins console output showed `Permission denied` immediately after the Set Permissions stage completed. Reviewing stage order revealed a duplicate `checkout scm` after permissions were set.

**Fix:** Only one `checkout scm` occurs, before the Set Permissions stage. No later stage calls `checkout scm` again.

**Verification:** Shell scripts execute successfully on Linux Jenkins agents.

**Prevention:** Ensure `checkout scm` is not called after `chmod +x`.

---

## Issue 7: Linux MYSQL.conf Not Found

**Problem:** Database configuration file was not found on Linux.

**Symptoms:**
```
config/linux/migration/MYSQL.conf
```

**Root Cause:** Linux filesystem paths are case-sensitive. The config file is named `mysql.conf` (lowercase), but the lookup used `MYSQL.conf` (uppercase).

**Where It Happened:** Configuration resolution on Linux

**How It Was Diagnosed:** `FileNotFoundError` for `MYSQL.conf` in Jenkins logs.

**Fix:** Lowercase normalization before path construction:

```bash
${DB_TYPE,,}
```

Mapping:
- `MYSQL` → `mysql`
- `MSSQL` → `mssql`
- `POSTGRESQL` → `postgresql`

**Verification:** Configuration files are found correctly on Linux with uppercase Jenkins parameters.

**Prevention:** Always normalize database type strings to lowercase before using them in filesystem paths on Linux.

---

## Issue 8: Linux echo. Command Not Found

**Problem:** Shell scripts failed with command not found errors.

**Symptoms:**
```
echo.: command not found
exit code 127
```

**Root Cause:** Windows batch syntax `echo.` was used inside a Linux `.sh` script.

**Where It Happened:** Linux shell scripts during pipeline execution

**How It Was Diagnosed:** Jenkins console output showed `command not found` for `echo.` with exit code 127.

**Fix:** Replace Windows batch syntax with Linux equivalents:

| Windows (Incorrect) | Linux (Correct) |
|---------------------|-----------------|
| `echo.` | `echo` or `printf '\n'` |
| `call script.bat` | `./script.sh` |
| `if errorlevel 1` | `if [ $? -ne 0 ]` |
| `.bat paths` | `.sh paths` |
| `%VARIABLE%` | `$VARIABLE` |

**Verification:** Shell scripts execute without syntax errors on Linux.

**Prevention:** Review all `.sh` files for Windows-only syntax before running on Linux.
