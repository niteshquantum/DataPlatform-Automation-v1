# 04 — Three Execution Modes

> This is the central concept of the platform. It is **verified from actual code**, not assumed.

## 1. Simple explanation (manager-ready)

Our automation has **one engine** but **three different ways to start it**:

1. **Main Jenkins** — a single Jenkins job where you pick the database, the action (setup / load / cleanup), and
   the cleanup mode. Jenkins decides which machine (Windows or Ubuntu) runs it.
2. **Standalone Jenkins** — a dedicated Jenkins job already locked to one database and one operating system, used
   for focused testing and debugging.
3. **Direct Local** — you run a `.bat` (Windows) or `.sh` (Linux) file on your laptop, with **no Jenkins at all**.

All three doors run the **same underlying scripts**, so the database ends up in the same state no matter which door
you used.

## 2. Technical explanation

The repository contains **three entry-point families**, but they converge on a **single shared core** of
Batch/Bash/PowerShell/Python scripts under `scripts/`.

| Mode | Entry artifact(s) | Agent/OS selection | DB/Action selection |
|------|-------------------|--------------------|---------------------|
| 1. Main Jenkins | `jenkins/Jenkinsfile` (root `agent none`) | Per-stage `agent { label 'windows-node' | 'ubuntu-node' }` | Build params `DATABASE`, `ACTION`, `CLEANUP_MODE` |
| 2. Standalone Jenkins | `jenkins/<db>/<os>/setup_pipeline.groovy`, `load_pipeline.groovy`, `cleanup_pipeline.groovy` | `agent any` (DB+OS fixed in the file name) | Hard-coded in the pipeline (no params) |
| 3. Direct Local | `scripts/batch/<db>/<db>_setup_pipeline.bat` / `..._load_pipeline.bat`; `scripts/bash/<db>/<db>_setup_pipeline.sh` | Determined by which file you run | Hard-coded in the file |

### The shared core (verified by tracing calls)

- Main Jenkins `PostgreSQL Setup` stage calls e.g. `scripts\batch\postgresql\setup\deploy_postgresql.bat`,
  `...create_database.bat`, `...run_liquibase.bat` — **the exact same `.bat` files** that
  `scripts/batch/postgresql/postgresql_setup_pipeline.bat` calls.
- The standalone `jenkins/postgresql/windows/setup_pipeline.groovy` stages also call
  `scripts\batch\postgresql\setup\*.bat`.
- Therefore **Mode 1, Mode 2, and Mode 3 share the same OS-layer scripts**, which in turn call Terraform,
  Liquibase, and Python. There is **no duplicate automation logic** for the three modes.

```
                    +------------------------------+
                    |   SHARED CORE AUTOMATION     |
                    |  scripts/batch|bash/<db>/...  |
                    |  + Terraform + Liquibase +   |
                    |    Python core + Database    |
                    +------------------------------+
                       ^            ^            ^
          calls same    |            |            |  calls same
           scripts      |            |            |   scripts
                       |            |            |
        +--------------+  +---------+  +---------+
        |                |            |           |
   Mode 1: Main      Mode 2:     Mode 3:     (etc.)
   Jenkins           Standalone  Direct Local
   Jenkinsfile       Jenkins     .bat / .sh
```

## 3. MOST IMPORTANT DISTINCTION

**These are THREE ENTRY / ORCHESTRATION METHODS OVER ONE SHARED CORE AUTOMATION — not three different
implementations.** Proven by the call graph: every entry point resolves to `scripts/batch|bash/<db>/...` scripts
that perform the real work (Terraform → Liquibase → Python → DB).

The only real differences between modes are:
- **Where the "which DB / which OS / which action" decision is made** (Jenkins params vs file choice vs filename).
- **Whether RBAC logging/reporting wrappers are present** (Jenkins adds `logger.py` + `generate_report.py`; the
  direct-local `.bat`/`.sh` pipelines do **not** currently invoke the logger/reporting — see status).
- **Whether a Jenkins agent label routes the work** (Mode 1 & 2 only).

## 4. When to use each mode

| Mode | Use when |
|------|----------|
| Main Jenkins | You want one job to control all databases/OS/actions centrally; you need RBAC + reports + build artifacts. |
| Standalone Jenkins | You are developing/testing a single database on a single OS and want isolated Jenkins feedback without affecting the master job. |
| Direct Local | You are debugging on your laptop, have no Jenkins, or want to reproduce a failing stage step-by-step. |

## 5. Advantages

- **Reuse:** one core, no logic duplication.
- **Consistency:** same scripts → same outcome regardless of entry point.
- **Flexibility:** central CI, isolated CI, or local dev.
- **RBAC + auditability** in Jenkins modes (execution log + HTML report per build).

## 6. Limitations

- Direct-local mode currently lacks the `logger.py`/`generate_report.py` reporting wrappers that Jenkins modes use.
- Direct-local `deploy_objects.bat` references `check_schema_changed.py`, which **does not exist** in the repo
  (would error before object generation). See `20_AS_BUILT_IMPLEMENTATION_STATUS.md`.
- Jenkinsfile hard-codes which DB runs on which OS node (e.g. PostgreSQL/MongoDB → Windows agent; MySQL/MSSQL →
  Ubuntu agent). It is not a free matrix.

## 7. Actual entry-point files

**Mode 1 — Main Jenkins**
- `jenkins/Jenkinsfile` (params: `DATABASE`, `ACTION`, `CLEANUP_MODE`, `USERNAME`, `PASSWORD`)

**Mode 2 — Standalone Jenkins** (24 pipelines verified)
- `jenkins/mysql/ubuntu/setup_pipeline.groovy`, `load_pipeline.groovy`, `cleanup_pipeline.groovy`
- `jenkins/mssql/ubuntu/setup|load|cleanup_pipeline.groovy`
- `jenkins/mssql/windows/setup|load|cleanup_pipeline.groovy`
- `jenkins/mongodb/ubuntu/setup|load|cleanup_pipeline.groovy`
- `jenkins/mongodb/windows/setup|load|cleanup_pipeline.groovy`
- `jenkins/postgresql/ubuntu/setup|load|cleanup_pipeline.groovy`
- `jenkins/postgresql/windows/setup|load|postgresql_cleanup_pipeline.groovy`
- `jenkins/mysql/windows/setup|load|mysql_cleanup.groovy` (note: MySQL Windows has **no** `setup_pipeline.groovy`
  for setup; only `setup_pipeline.groovy` is present — see matrix below)

**Mode 3 — Direct Local**
- Windows: `scripts/batch/<db>/<db>_setup_pipeline.bat`, `<db>_load_pipeline.bat` (e.g. `postgresql_setup_pipeline.bat`, `postgresql_load_pipeline.bat`)
- Ubuntu: `scripts/bash/<db>/<db>_setup_pipeline.sh`, `<db>_load_pipeline.sh`

## 8. Standalone pipeline coverage matrix

| Database | OS | Standalone Setup | Standalone Load | Standalone Cleanup | Status |
|----------|----|------------------|-----------------|--------------------|--------|
| MySQL | Ubuntu | setup_pipeline.groovy | load_pipeline.groovy | cleanup_pipeline.groovy | COMPLETE |
| MySQL | Windows | setup_pipeline.groovy | load_pipeline.groovy | mysql_cleanup.groovy | COMPLETE (note naming) |
| PostgreSQL | Ubuntu | setup_pipeline.groovy | load_pipeline.groovy | cleanup_pipeline.groovy | COMPLETE |
| PostgreSQL | Windows | setup_pipeline.groovy | load_pipeline.groovy | postgresql_cleanup_pipeline.groovy | COMPLETE |
| MSSQL | Ubuntu | setup_pipeline.groovy | load_pipeline.groovy | cleanup_pipeline.groovy | COMPLETE |
| MSSQL | Windows | setup_pipeline.groovy | load_pipeline.groovy | cleanup_pipeline.groovy | COMPLETE |
| MongoDB | Ubuntu | setup_pipeline.groovy | load_pipeline.groovy | cleanup_pipline.groovy | COMPLETE (typo in filename) |
| MongoDB | Windows | setup_pipeline.groovy | load_pipeline.groovy | mongodb_cleanup.groovy | COMPLETE |

> The Main Jenkinsfile only wires MySQL/MSSQL on Ubuntu and MongoDB/PostgreSQL on Windows (see §9). Standalone
> pipelines exist for more DB/OS combinations than the main pipeline currently routes.

## 9. Main Jenkins DB→OS routing (verified)

| Stage | DB | Action | Agent label |
|-------|----|--------|-------------|
| MySQL Setup / Load / Cleanup | MYSQL | SETUP/LOAD/CLEANUP | `ubuntu-node` |
| MSSQL Setup / Load / Cleanup | MSSQL | SETUP/LOAD/CLEANUP | `ubuntu-node` |
| MongoDB Setup / Load / Cleanup | MONGODB | SETUP/LOAD/CLEANUP | `windows-node` |
| PostgreSQL Setup / Load / Cleanup | POSTGRESQL | SETUP/LOAD/CLEANUP | `windows-node` |

## 10. 30-second explanation

> "We have one automation engine and three ways to press the button: a central Jenkins job where you pick the
> database and action, a dedicated Jenkins job for one database/OS, or a script you run on your laptop. All three
> run the exact same underlying scripts, so the result is identical. Jenkins adds security (RBAC) and reports."

## 11. 2-minute explanation

The platform's value is repeatability. Installing and configuring a database, deploying its schema, loading data,
and creating objects is the same work every time, yet easy to get wrong manually. We encoded that work as shared
scripts. Instead of copying those scripts into three places, we built three **entry points** (Jenkins main,
Jenkins standalone, local script) that all call the same scripts. Jenkins decides which physical machine (Windows
agent vs Ubuntu agent) runs a stage. Terraform installs/starts the database locally, Liquibase deploys schema and
objects, Python loads the dataset and runs discovery/assessment, and every Jenkins run produces an execution log
and an HTML report. RBAC sits in front of Jenkins to allow or deny the requested database.action.
