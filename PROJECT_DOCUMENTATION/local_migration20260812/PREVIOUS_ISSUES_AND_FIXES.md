# Previous Issues and Fixes — Windows Migration Pipeline

## Issue 1: Production Liquibase Files Were Involved in Migration

**Problem:** Migration testing initially wrote generated changelogs and applied changes directly into the production Liquibase directories (`liquibase/mysql/`, `liquibase/mssql/`, `liquibase/postgresql/`). This risked corrupting production artifacts and altering existing `DATABASECHANGELOG` checksums.

**Fix:** A migration-specific Liquibase directory was introduced:

```
liquibase/migration/<database>/
```

Migration Stage 5 now generates directly into this isolated directory. Production Liquibase directories remain separate and untouched.

---

## Issue 2: Liquibase Checksum Mismatch

**Problem:** Validation failed with errors such as:

```
Validation Failed:
changesets check sum
```

This occurred because previous test runs left `DATABASECHANGELOG` entries whose stored checksum no longer matched the changed migration XML files.

**Fix:** This is not a code defect. Using a clean destination database state and isolated migration changelogs (`liquibase/migration/<database>/`) resolves the testing problem.

---

## Issue 3: Destination Database Did Not Exist

**Problem:** The pipeline initially attempted to connect directly to a missing destination database, causing connection failures during local testing.

**Fix:** Destination validation was changed to:

```
check existence
→ bootstrap connection
→ create database
→ reconnect
→ validate
```

---

## Issue 4: Migration Pipeline Used Production Liquibase Runners/Configuration

**Problem:** Migration execution reused the production Liquibase runner and configuration paths, mixing migration artifacts with production setup.

**Fix:** A migration-specific Liquibase runner and configuration were introduced. Migration execution now uses:

- **Config:** `config/windows/migration/`
- **Liquibase output:** `liquibase/migration/<database>/`

instead of the production setup paths.
