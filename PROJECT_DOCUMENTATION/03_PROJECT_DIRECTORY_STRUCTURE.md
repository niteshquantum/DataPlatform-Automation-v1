# 03 — Project Directory Structure

> Only `docs/` is excluded from architecture analysis (legacy/out-of-scope, intentionally not used as a source).

## Top-level layout (as built)

| Path | Role | Classification |
|------|------|----------------|
| `config/` | `.conf` files for DB + OS + common settings | CONFIG (source of truth for connections) |
| `databases/` | MSSQL `ConfigurationFile.template.ini` only | TEMPLATE |
| `failed/` | Failed run artifacts per DB (mostly empty `.gitkeep`) | OUTPUT / FAILURE |
| `jenkins/` | `Jenkinsfile` + per-DB/OS `setup|load|cleanup_pipeline.groovy` | ENTRY POINT |
| `liquibase/` | `master.xml` per DB + `objects/custom/` placeholders | CONFIG (runtime regenerated) |
| `metadata/` | Discovery/assessment/reconciliation outputs per DB | GENERATED |
| `objects/` | Per-DB `custom/<type>/` folders (input objects, mostly empty) | SOURCE (object inputs) |
| `outputs/` | `assessments/` per DB (assessment results) | GENERATED |
| `rbac/` | `auth.py`, `cli.py`, `authorization.py`, `utils.py`, JSON creds/roles/perms | SOURCE (security) |
| `requirements/` | `common.txt` + per-DB `.txt` Python requirements | CONFIG |
| `scripts/` | All automation: `batch/`, `bash/`, `powershell/`, `python/`, engines | SOURCE (core) |
| `terraform/` | Per-DB `main.tf`/`variables.tf`/`terraform.tfvars` (local-exec) | CONFIG |
| `tools/` | `.gitkeep` placeholders for `liquibase/`, `terraform/`, `drivers/` | RUNTIME DEPENDENCY (downloaded) |
| `archive/` | Per-DB archive folders (empty) | OUTPUT |
| `docs/` | **Legacy / out-of-scope documentation — NOT used as architecture source** | EXCLUDED |

## `scripts/` subtree (the working core)

| Subtree | Responsibility |
|---------|----------------|
| `scripts/batch/` | Windows orchestration (`.bat`) + thin wrappers to PowerShell/Python |
| `scripts/bash/` | Ubuntu orchestration (`.sh`) |
| `scripts/powershell/` | Windows-native install/configure/cleanup logic (`.ps1`) |
| `scripts/python/` | Cross-OS Python: `common/` (config, objects, logging), per-DB setup/load/assessment |
| `scripts/<engine>.py` | Top-level engines: `data_loader.py`, `run_liquibase.py` (legacy), `schema_detector.py`, discovery/assessment/reconciliation/recommendation/governance/cdc |
| `scripts/logging/` | `logger.py` execution-log writer |
| `scripts/reporting/` | `generate_report.py`, `generate_history.py`, migration reports |

## Important folders explained

- **`config/`** — the single place where host/port/db/user/password/version/driver/liquibase versions live. Read by
  `config_loader.py` (Python) and parsed line-by-line by `.bat`/`.sh` scripts.
- **`tools/`** — intentionally empty placeholders (`liquibase/`, `terraform/`, `drivers/`); install scripts download
  binaries here. Pipelines fail fast if `tools/terraform/terraform[.exe]` or `tools/liquibase/liquibase[.bat]` missing.
- **`objects/`** — drop-zone for **custom** DB objects (views, functions, etc.). The automation also *generates*
  objects from schema metadata at runtime under `objects/<db>/generated/`.
- **`liquibase/`** — `master.xml` is the schema entry point; `master_objects.xml` is generated at runtime for
  objects. `objects/custom/` folders are placeholders.
- **`metadata/`** — machine-written outputs (discovery, profiling, assessment, reconciliation, recommendation,
  governance, CDC history). Created/read by Python engines.
- **`failed/` & `archive/`** — named by DB; used by the data loader (`.error.log`, moved files). Mostly empty in
  the repo because they are populated at runtime.

## What `docs/` is

Legacy / out-of-scope documentation. Per project rules it was **not** used as a source of truth and **not** modified.
