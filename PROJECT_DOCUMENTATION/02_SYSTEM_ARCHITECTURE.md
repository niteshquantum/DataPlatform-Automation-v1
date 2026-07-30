# 02 — System Architecture

## 1. Layered architecture (as built)

```mermaid

+----------------------------------------------------------------------+
|                         EXECUTION ENTRY LAYER                        |
|                                                                      |
|  Mode 1: jenkins/Jenkinsfile            (agent none -> routes)      |
|  Mode 2: jenkins/<db>/<os>/*.groovy       (standalone jobs)         |
|  Mode 3: scripts/batch|bash/<db>/*pipeline.(bat|sh) (local)         |
+----------------------------------------------------------------------+
                              |
                              v
+----------------------------------------------------------------------+
|                      OS ORCHESTRATION LAYER                         |
|  Windows: .bat  -> PowerShell (.ps1) -> Python                       |
|  Ubuntu : .sh   -> Bash -> Python                                   |
+----------------------------------------------------------------------+
                              |
                              v
+----------------------------------------------------------------------+
|                         SHARED CORE LAYER                           |
|  - config_loader.py (reads config/<os>/<db>.conf)                   |
|  - Terraform provisioners (local-exec)                              |
|  - Liquibase runners (apply master.xml / master_objects.xml)        |
|  - Python engines: data_loader, object generators, discovery,       |
|    assessment, reconciliation, recommendation, governance, cdc      |
|  - RBAC (auth_cli.py, cli.py)                                       |
|  - logging/logger.py, reporting/generate_report.py                  |
+----------------------------------------------------------------------+
                              |
                              v
+----------------------------------------------------------------------+
|                       TARGET RESOURCES                              |
|  (local) Terraform state  -> installs DB binaries                   |
|  Liquibase            -> creates schema / objects                   |
|  Python loaders       -> inserts dataset rows                      |
|  Database instances   -> MySQL / PostgreSQL / MSSQL / MongoDB      |
+----------------------------------------------------------------------+
                              |
                              v
+----------------------------------------------------------------------+
|                       OUTPUT / EVIDENCE LAYER                       |
|  logs/<db>/<action>/build_N/execution.json                         |
|  reports/<db>/<action>/build_N/report.{json,html}                   |
|  metadata/<area>/<db>/...   archive/  failed/  outputs/assessments/ |
+----------------------------------------------------------------------+
```

## 2. Control vs execution nodes (Jenkins)

- The **Jenkins controller** hosts the job definitions (`Jenkinsfile`, standalone `.groovy`).
- With `agent none` at the pipeline root, the master Jenkinsfile itself runs no heavy work; each `stage` declares
  its own `agent { label 'windows-node' }` or `agent { label 'ubuntu-node' }`.
- Actual commands (`.bat` / `.sh`) execute on the **Jenkins agent node** that matches the label — i.e. a Windows
  agent for PostgreSQL/MongoDB stages, an Ubuntu agent for MySQL/MSSQL stages in the current main pipeline.
- This means the controller can run on one OS while the database work runs on a different OS agent.

> VERIFIED from `jenkins/Jenkinsfile`: the master pipeline uses `agent none` and per-stage `windows-node` /
> `ubuntu-node` labels.

## 3. Key architectural decisions (observed in code)

| Decision | Evidence | Rationale |
|----------|----------|-----------|
| One shared core, three entry points | Main Jenkins, standalone `.groovy`, and `*.bat`/`*.sh` all call the same `scripts/batch|bash/<db>/...` scripts | Consistency + reuse |
| Config by OS + DB | `config/windows/*.conf`, `config/ubuntu/*.conf` | OS-specific paths/ports |
| Terraform for local provisioning only | `terraform/*/main.tf` uses `null_resource` + `local-exec` | Automate install/start without cloud |
| Liquibase for schema + objects | `run_liquibase.bat/.sh` applies `master.xml` and `master_objects.xml` | Versioned, repeatable schema |
| RBAC gate before execution | `Jenkinsfile` calls `auth_cli.py` then `cli.py` | Least-privilege control |
| Reports from a JSON log | `logger.py` writes `execution.json`; `generate_report.py` renders HTML | Auditable per-build evidence |

## 4. Component interaction summary

- **Jenkinsfiles** → call `bat`/`sh` scripts (OS layer).
- **bat/sh pipelines** → validate runtime, call Terraform (`deploy_*.bat`/`deploy_*.sh`), call Liquibase
  (`run_liquibase`), call Python loaders/generators.
- **Python core** → reads `config`, connects to DB, writes `metadata`, moves files between `incoming/archive/failed`
  (note: `incoming/` is referenced by `data_loader.py` but not present in the repo — see status doc).
- **RBAC** → gates every Jenkins entry point.
- **Logging/Reporting** → wrap every run, producing `logs/` and `reports/`.

## 5. Scope boundaries

- Terraform **does not provision cloud infrastructure**; it orchestrates **local** install/start via
  `local-exec` provisioners only.
- Liquibase changelogs are **generated at runtime** (`master.xml` for load, `master_objects.xml` for objects); the
  committed `master.xml` files are essentially empty placeholders.
- RBAC is **file-based** (JSON) and **not** integrated with the database's own users/privileges beyond the gate.
