# 23 — Demo and Explanation Guide

Practical guide for the project owner to explain and demo the platform confidently.

## 1. Project in one line

> A cross-operating-system, Jenkins-orchestrated automation framework that provisions and configures four
> databases, deploys schema via Liquibase, loads datasets, generates and deploys database objects, enforces
> role-based access control, and validates outcomes — all driven by shared Python/Batch/Bash scripts.

## 2. Project in 30 seconds (manager)

"We built one automation engine that installs a database, builds its schema, loads data, creates its objects
(views, procedures, etc.), applies security roles, and proves it worked — for MySQL, PostgreSQL, SQL Server,
and MongoDB, on both Windows and Linux. You can launch it three ways: one central Jenkins job, a focused
Jenkins job per database, or a script on your laptop. All three run the same scripts, so the result is identical,
and every run produces a report."

## 3. Project in 2 minutes (technical)

- **Problem:** Database setup/schema/data/objects/RBAC is repetitive and error-prone; teams redo it per migration.
- **Solution:** Codify each step as reusable, parameterized, cross-OS scripts.
- **Architecture:** Three entry points → one shared core (Batch/Bash/PowerShell/Python) → Terraform (install/start),
  Liquibase (schema+objects), Python (load + analytics) → Database.
- **Databases:** MySQL, PostgreSQL, SQL Server, MongoDB.
- **OS:** Windows (Batch+PowerShell), Ubuntu (Bash).
- **Jenkins:** Central + standalone pipelines, RBAC gate, per-build reports.
- **Terraform:** Local provisioning via `null_resource` `local-exec` (not cloud).
- **Liquibase:** Versioned schema + object changelogs.
- **Objects:** Detected/generated from metadata, deployed via Liquibase.
- **RBAC:** File-based auth + authorization gate before execution.
- **Validation:** Runtime/env/schema/data/object checks + execution log.

## 4. Three execution modes (30-second)

"Our automation has three ways to start, but only one engine. **Main Jenkins** is one job where you pick the
database, action, and cleanup mode, and Jenkins picks the right machine. **Standalone Jenkins** is a dedicated
job already locked to one database and OS, for isolated testing. **Direct Local** is a `.bat`/`.sh` you run on
your laptop with no Jenkins. All three call the same underlying scripts, so the outcome is the same."

## 5. Why three execution modes?

- **Centralized orchestration** (Main Jenkins) — control everything from one parameterized job.
- **Independent testing** (Standalone) — test one DB/OS without touching the master job.
- **Local debugging** (Direct Local) — reproduce/debug a failing stage on a laptop, no Jenkins.
- **Jenkins-independent execution** — automation works even without CI.
- **Reuse of core automation** — no duplicated logic; one set of scripts everywhere.

## 6. Technology — one line each

- **Jenkins** = CI/CD orchestrator that routes work to Windows/Ubuntu agents and enforces RBAC.
- **Terraform** = runs local install/start scripts for the database (local-exec, not cloud).
- **Liquibase** = applies versioned schema and object changelogs to the database.
- **Python** = the cross-OS brain: config, data loading, object generation, discovery, reporting.
- **PowerShell** = Windows-native install/configure/cleanup logic.
- **Batch** = Windows orchestration sequencing of phases.
- **Bash** = Ubuntu orchestration sequencing of phases.
- **RBAC** = authentication + authorization gate in front of Jenkins runs.
- **Metadata** = machine-written knowledge store (profiling, discovery, assessment, reconciliation).

## 7. Recommended demo order

1. Project structure (`03_PROJECT_DIRECTORY_STRUCTURE.md`, `config/`, `scripts/`).
2. Config (`config/windows/postgresql.conf`) — how it knows host/port/creds.
3. Three execution modes (`04_THREE_EXECUTION_MODES.md`).
4. Main Jenkins (`jenkins/Jenkinsfile`) — params + agent routing.
5. Run flow (SETUP → LOAD) tracing `postgresql_setup_pipeline.bat`.
6. Liquibase (`run_liquibase.bat`, `liquibase/postgresql/master.xml` + runtime `master_objects.xml`).
7. Objects (`bootstrap_generator.py`, `deploy_objects.py`).
8. RBAC (`rbac/cli.py`, `roles.json`, `permissions.json`).
9. Validation (`validate_*.bat`, `logger.py` → `report.html`).
10. Outputs (`logs/`, `reports/`, `metadata/`, `failed/`).

## 8. What to say while demonstrating

| Step | Open | Point at | Say | Do NOT claim |
|------|------|----------|-----|----------------|
| Structure | `scripts/` tree | `batch`/`bash`/`python` | "One core, OS-specific wrappers" | "Fully symmetric across DBs" |
| Config | `config/windows/postgresql.conf` | host/port/password keys | "Single source for connections" | "Secrets are encrypted" |
| Modes | `04` doc + three entry files | `Jenkinsfile`, `*.groovy`, `*.bat` | "Three doors, one engine" | "Three separate implementations" |
| Main Jenkins | `Jenkinsfile` | params + `agent { label }` | "Picks Windows/Ubuntu node" | "Runs on controller directly" |
| Liquibase | `run_liquibase.bat` | driver jar + changelog | "Versioned schema apply" | "changelogs are committed" |
| Objects | `bootstrap_generator.py` | `database_objects.json` | "Generated, not hand-written" | "Custom objects are pre-loaded" |
| RBAC | `rbac/roles.json` | permission keys | "Gate before automation" | "Creates DB users" |
| Reports | `reports/.../report.html` | stage table | "Auditable per build" | "Present in local mode too" |

## 9. Common questions (manager/senior)

- **Why Jenkins?** Central orchestration, agent routing (Windows/Ubuntu), RBAC, and per-build reports/artifacts.
- **Why Terraform?** One declarative, re-runnable command to install/start the DB locally via scripts.
- **Why Liquibase?** Versioned, repeatable, idempotent schema/object application with a lock table.
- **Why Python?** Cross-OS core logic (load, generate, discover) shared by both operating systems.
- **Why separate Windows/Ubuntu scripts?** Different install/configure models (PowerShell services vs Bash).
- **Why three execution methods?** Central CI, isolated CI testing, and Jenkins-free local debugging — one core.
- **Why not one giant script?** Separation = testability, OS specialization, and reuse across entry points.
- **How do databases differ?** Object support varies (e.g. PG has materialized views/extensions; MySQL has events;
  Mongo has collections/indexes, no Liquibase). See `05_DATABASE_SUPPORT_MATRIX.md`.
- **How is it reusable?** Same scripts driven by `config/<os>/<db>.conf`; add a DB by adding conf + scripts.
- **How is failure handled?** Per-phase exit codes abort the chain; Jenkins records stage status + error in a report.
- **How do you validate success?** Post-load row counts, object validators, and the HTML execution report.
- **What is RBAC?** File-based authentication + authorization gate allowing/denying `<db>.<action>`.
- **What are database objects?** Views, procedures, functions, triggers, indexes, etc., generated + deployed.
- **What is metadata used for?** Stores profiling/discovery/assessment/reconciliation for migration analytics.
- **What is currently incomplete?** Missing `check_schema_changed.py` (breaks local object deploy); legacy unused
  `run_liquibase.py`; RBAC/reporting not wired into local mode; `tools/`+`incoming/` are runtime inputs.
  See `20_AS_BUILT_IMPLEMENTATION_STATUS.md`.

## 10. Architecture explanation without code

Imagine a single, well-built machine that can stand up any of four databases, build their structure, pour in data,
add the advanced pieces (views, procedures), lock down who can do what, and then check its own work. We built
three different doorways into that machine — a control room (Jenkins), a focused side door (standalone Jenkins),
and a manual handle (a script). Whoever enters, the machine does the same reliable job and prints a report.

## 11. Technical architecture explanation

Entry layer (Jenkinsfile / standalone `.groovy` / local `.bat`/`.sh`) → OS orchestration layer
(Batch→PowerShell on Windows, Bash on Ubuntu) → shared core (config_loader, Terraform local-exec provisioners,
Liquibase runners, Python engines for loading/generation/discovery) → target database + evidence outputs
(logs, reports, metadata, archive/failed). Jenkins adds an RBAC gate and structured logging/reporting; Terraform
and Liquibase provide idempotent provisioning and schema/object management.

## 12. Important claims to avoid

- Do NOT claim `check_schema_changed.py` works (file is absent; local object deploy will error).
- Do NOT claim `run_liquibase.py` is the active runner (legacy/unused).
- Do NOT claim changelogs are committed (they are generated at runtime).
- Do NOT claim RBAC/reporting run in local mode (only wired into Jenkins).
- Do NOT claim secrets are encrypted (DB passwords are plaintext in `.conf`).
- Do NOT claim all four DBs are equally complete on both OSs in the main pipeline (routing is partial).
- Do NOT claim cloud infrastructure is provisioned (Terraform is local-exec only).
