# How to Explain This

## Elevator Pitch (30 seconds)

> "We have a Jenkins pipeline that automatically migrates database schemas from one database type to another. You trigger it with a few parameters — source database, destination database, and connection details. It validates both databases, extracts the source schema, generates version-controlled DDL using Liquibase, and applies it to the destination. The whole process takes a few minutes and is safe to re-run."

## Key Points by Question

### Q: What does this pipeline do?

It performs **automated cross-database schema migration**. Given a source database (e.g., MSSQL) and a destination database (e.g., MySQL), it:
1. Validates both databases are reachable
2. Extracts the source schema (tables and columns)
3. Generates Liquibase changelog files for the destination
4. Applies the changelog to create the schema on the destination

### Q: Why not just use a manual export/import?

Because manual migration is:
- Error-prone (missed tables, wrong data types)
- Not repeatable (no version control)
- Not auditable (no change history)
- Not idempotent (hard to re-run safely)

The pipeline uses Liquibase, which provides:
- Version-controlled DDL
- Checksum validation
- Idempotent execution (safe to re-run)
- Preconditions (only create what doesn't exist)

### Q: What databases does it support?

Currently three: **MSSQL**, **MySQL**, and **PostgreSQL**. Any combination is supported except same-type migration (e.g., MSSQL to MSSQL is blocked).

### Q: How do I trigger a migration?

You go to the Jenkins job, click "Build with Parameters", and fill in:
- **Source database type** (MSSQL / MySQL / PostgreSQL)
- **Destination database type**
- **Connection details** (host, port, database name, user, password)

If you leave connection fields empty, the pipeline uses pre-configured defaults from the project's config files.

### Q: What happens if the destination database doesn't exist?

The pipeline **automatically creates it**. You don't need to manually create the database first. It will never drop an existing database.

### Q: Is this safe to run against production?

**Not without review.** The pipeline is designed for migration testing and development. Before running against production:
1. Review the generated Liquibase changelogs
2. Test in a staging environment first
3. Understand the data implications of schema changes

### Q: What is Liquibase and why do we use it?

Liquibase is a **database schema version control tool**. It tracks which changes have been applied to a database via a `DATABASECHANGELOG` table. This means:
- You know exactly what schema version a database is at
- You can roll back changes
- You can audit who applied what and when
- You can safely re-run migrations (preconditions handle existing objects)

### Q: How long does a typical migration take?

For a schema-only migration (no data transfer), typically **2-5 minutes** depending on:
- Number of tables
- Database server responsiveness
- Network latency to the database

### Q: What if something goes wrong?

The pipeline stops at the failing stage and reports the error. Common issues:
- Database not running → Start the database server
- Wrong credentials → Verify host, port, user, password
- Missing JDBC driver → The pipeline installs drivers automatically, but you can verify in `tools/drivers/`
- Checksum mismatch → Use a fresh test database

### Q: Can I run this locally?

Yes. The same Python modules work on both Windows and Linux. The batch wrappers (`.bat`) are Windows-specific, but the core logic is in shared Python files. On Linux, shell wrappers (`.sh`) are used instead.

### Q: What is the "source.conf" and "destination.conf"?

These are **configuration files** that define which database types to use as source and destination. They live in `config/windows/migration/` (or `config/linux/migration/`). You can override any field from the Jenkins UI without editing these files.

### Q: How do I know what the pipeline will do before running it?

The **Initialize Migration** and **Validate** stages show you exactly what source and destination will be used, including host, port, database name, and user. You can review these before the pipeline proceeds to schema extraction.

## One-Slide Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│              WINDOWS DATABASE MIGRATION PIPELINE                    │
├─────────────────────────────────────────────────────────────────────┤
│  TRIGGER: Jenkins "Build with Parameters"                           │
│                                                                     │
│  INPUT:  Source DB type + Destination DB type + Connection details │
│          (or use pre-configured defaults)                           │
│                                                                     │
│  STAGES:                                                            │
│    1. Initialize   → Resolve config, validate endpoints            │
│    2. Validate Src → Test source connection                        │
│    3. Validate Dst → Test destination, auto-create if missing      │
│    4. Extract      → Read source tables/columns → metadata/        │
│    5. Generate DDL  → metadata/ → Liquibase XML changelogs         │
│    6. Install LB    → Ensure Liquibase is available                │
│    7. Install Drv   → Ensure JDBC drivers are available            │
│    8. Apply Schema  → Liquibase applies changelog to destination   │
│                                                                     │
│  OUTPUT: Destination database with source schema                    │
│                                                                     │
│  SAFETY:  • Never drops existing databases                         │
│           • Isolated Liquibase directories (no prod contamination) │
│           • Idempotent execution (safe to re-run)                  │
│           • Prevents same-endpoint migration                       │
└─────────────────────────────────────────────────────────────────────┘
```
