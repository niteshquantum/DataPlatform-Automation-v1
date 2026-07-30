# 11 — Liquibase Schema Automation

## What Liquibase does here

Liquibase applies **versioned schema changelogs** to the target database. It is invoked by the OS-layer
runners (`run_liquibase.bat` / `run_liquibase.sh`) which the Jenkins/batch/bash pipelines call during setup
and object deployment.

## Entry points (verified)

| Runner | OS | What it runs |
|--------|----|--------------|
| `scripts/batch/<db>/setup/run_liquibase.bat` | Windows | `tools/liquibase/liquibase.bat` with `--changeLogFile` |
| `scripts/bash/<db>/setup/run_liquibase.sh` | Ubuntu | `tools/liquibase/liquibase` with `--changeLogFile` |

Both read `config/<os>/<db>.conf` for host/port/db/user/password/driver version, validate the Liquibase
binary + JDBC driver jar, then run `liquibase update`.

Example (PostgreSQL Windows): driver `tools/drivers/postgresql-<POSTGRESQL_DRIVER_VERSION>.jar`,
changelog default `liquibase\postgresql\master.xml`, JDBC `org.postgresql.Driver`.

## Master changelog

- `liquibase/<db>/master.xml` is the **schema entry point**.
- In the repository it is a near-empty placeholder (`<databaseChangeLog>` with only a comment). The real, dataset-specific
  includes are **generated at runtime** by the load flow (see `update_master_xml.py`) and are not committed.
- `liquibase/<db>/master_objects.xml` is **generated at runtime** by `bootstrap_generator.py` /
  `generate_master_objects.py` for database objects.

## Flow (verified in `load_data.sh`)

```
schema_detector.py            -> read schema metadata
generate_liquibase_xml.py   -> create dataset changelog XML
update_master_xml.py         -> rewrite master.xml with <include> of generated changelog
run_liquibase.sh/.bat      -> liquibase update (applies schema)
```

## Objects integration

- Object generators (`generate_liquibase_objects.py`, `xml_generators/*`) emit Liquibase XML changesets into
  `liquibase/<db>/objects/`.
- `generate_master_objects.py` builds `liquibase/<db>/master_objects.xml` referencing them.
- `deploy_objects.py` calls the DB/OS `run_liquibase` runner with `master_objects.xml`.

## Tables managed

Liquibase maintains `DATABASECHANGELOG` and `DATABASECHANGELOGLOCK` (standard). Rollback scripts
were **not found** in the repo (no `rollback` targets wired into runners).

## Why Liquibase instead of raw SQL

- Versioned, repeatable, idempotent schema application (locked via `DATABASECHANGELOGLOCK`).
- Generated changelogs keep schema in step with detected dataset metadata.
- One command (`liquibase update`) across MySQL/PostgreSQL/MSSQL with DB-specific drivers.

## Legacy note

`scripts/run_liquibase.py` is a **standalone legacy script** that hardcodes MySQL, reads a non-existent
`config/mysql.conf` (Windows) and scans `liquibase/generated/` (which does not exist). The active pipelines
do **not** use it; they use the `run_liquibase.bat/.sh` runners instead.

## Status

- Schema deployment via runners: **IMPLEMENTED**. Runtime-generated changelogs: **IMPLEMENTED** (not verified at runtime).
- MongoBD: **NOT APPLICABLE** (document store).
