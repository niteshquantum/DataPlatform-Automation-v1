# 21 — Developer Runbook

> Commands are derived from actual scripts in the repo. Do not invent commands. No runtime execution
> was performed to verify these; they reflect the wired call chains.

## Prerequisites

- Python 3 (validated by `validate_python_runtime.bat/.sh`).
- Java (for Liquibase; `validate_java_runtime`).
- Terraform binary at `tools/terraform/terraform[.exe]` (installed by `install_terraform.*`).
- Liquibase at `tools/liquibase/liquibase[.bat]` (installed by `install_liquibase.*`).
- JDBC driver jar at `tools/drivers/<db>-<ver>.jar` (installed by `install_*_driver.*`).
- Populate `incoming/<db>/` with CSV/JSON before LOAD (referenced by `data_loader.py`).

## Quick start — direct local (Windows, PostgreSQL setup)

```
scripts\batch\postgresql\postgresql_setup_pipeline.bat
```

## Quick start — direct local (Ubuntu, PostgreSQL setup)

```
bash scripts/bash/postgresql/postgresql_setup_pipeline.sh
```

## Setup (per DB/OS)

| DB | OS | Command |
|----|----|----------|
| PostgreSQL | Win | `scripts\batch\postgresql\postgresql_setup_pipeline.bat` |
| PostgreSQL | Ubuntu | `bash scripts/bash/postgresql/postgresql_setup_pipeline.sh` |
| MySQL | Ubuntu | `bash scripts/bash/mysql/mysql_setup_pipeline.sh` |
| MSSQL | Win | `scripts\batch\mssql\mssql_setup_pipeline.bat` |
| MSSQL | Ubuntu | `bash scripts/bash/mssql/mssql_setup_pipeline.sh` |
| MongoDB | Win | `scripts\batch\mongodb\mongodb_setup_pipeline.bat` |
| MongoDB | Ubuntu | `bash scripts/bash/mongodb/mongodb_setup_pipeline.sh` |

## Load

```
scripts\batch\postgresql\postgresql_load_pipeline.bat
bash scripts/bash/postgresql/postgresql_load_pipeline.sh
```

## Objects (after setup/load)

```
scripts\batch\postgresql\objects\deploy_objects.bat   (generate + deploy + validate)
```
> NOTE: `deploy_objects.bat` calls `check_schema_changed.py`, which is **absent** from the repo. This step
> will error in direct-local mode. Use the standalone Jenkins job or call `bootstrap_generator.py` +
> `deploy_objects.py` directly until the file is added.

## RBAC (Jenkins only)

```
python rbac/auth_cli.py --username <u> --password <p>
python rbac/cli.py --username <u> --password <p> --permission "postgresql.setup"
```

## Validation / reporting

- Reports are produced by Jenkins via `generate_report.py` + `generate_history.py`.
- In local mode, inspect console output of `validate_*.bat/.sh` and the data loader's `failed/<db>/` logs.

## Jenkins

- Main job: `jenkins/Jenkinsfile` → parameters `DATABASE`, `ACTION`, `CLEANUP_MODE`, `USERNAME`, `PASSWORD`.
- Standalone: create a Jenkins job from `jenkins/<db>/<os>/<phase>_pipeline.groovy`.
- Agents must carry labels `windows-node` / `ubuntu-node` matching the main pipeline's per-stage routing.
