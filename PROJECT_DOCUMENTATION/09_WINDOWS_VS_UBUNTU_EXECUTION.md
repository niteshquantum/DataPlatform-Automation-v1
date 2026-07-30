# 09 — Windows vs Ubuntu Execution

## Why four script types exist

| Layer | Windows | Ubuntu | Responsibility |
|-------|---------|--------|----------------|
| Orchestration | `.bat` (`scripts/batch/`) | `.sh` (`scripts/bash/`) | Sequence the phases, set `PROJECT_ROOT`, call children, `exit /b` on error |
| Native OS | `.ps1` (`scripts/powershell/`) | (Bash directly) | Windows-native install/configure/cleanup that Batch can't do cleanly |
| Core logic | `Python` (`scripts/python/`) | `Python` (same files) | Cross-OS engine: config, loaders, generators, discovery |

Windows uses **three layers** (`.bat` → `.ps1`/Python) because installing/configuring SQL Server, PostgreSQL, and
MongoDB on Windows needs PowerShell (services, ACLs, installers). Ubuntu uses **two layers** (`.sh` → Python)
because Bash handles native install/start directly.

## Windows orchestration

- Entry: `scripts/batch/<db>/<db>_setup_pipeline.bat`, `<db>_load_pipeline.bat`.
- `set_project_root.bat` computes `PROJECT_ROOT` and fails fast if `config/` missing.
- Each phase is a `call` to a `scripts/batch/<db>/<phase>/*.bat`; `if errorlevel 1 exit /b 1` aborts the pipeline
  on first failure.
- `.bat` scripts that need Windows-native work shell out to PowerShell: e.g.
  `download_dataset.bat` → `powershell.exe -File download_dataset.ps1`; `deploy_postgresql.bat` → Terraform →
  `powershell/postgresql/install_windows.ps1`.
- Admin-branching: `check_admin_privileges.bat` return code decides service vs project-local mode
  (MongoDB/PostgreSQL).

## Ubuntu orchestration

- Entry: `scripts/bash/<db>/<db>_setup_pipeline.sh`, `<db>_load_pipeline.sh`.
- `set -e` + `source set_project_root.sh` (realpath).
- Each phase is `bash "$PROJECT_ROOT/scripts/bash/<db>/<phase>/*.sh"`.
- Terraform `null_resource` local-exec calls `scripts/bash/<db>/setup/install_postgresql.sh` (and start/validate).

## Shared cross-platform logic

- **Python** is the single cross-OS core. Same `.py` files run on both OS.
- `config_loader.py` selects `config/windows/*.conf` vs `config/ubuntu/*.conf` via `platform.system()`.
- `data_loader.py` picks driver + quoting by `db_type` (mysql/postgresql/mssql) and uses `pyodbc`/`psycopg2`/
  `mysql.connector`.
- `deploy_objects.py` branches runner path by `platform.system()` (windows `.bat` vs linux `bash`).

## Capability matrix (Windows | Ubuntu | Shared)

| Capability | Windows | Ubuntu | Shared logic |
|------------|---------|--------|--------------|
| Project root resolution | `set_project_root.bat` | `set_project_root.sh` | both compute repo root |
| Runtime validation | `validate_*.bat` | `validate_*.sh` | Python validators |
| DB install/start | Terraform → `.ps1` | Terraform → `.sh` | `terraform/*/main.tf` |
| Liquibase apply | `run_liquibase.bat` | `run_liquibase.sh` | `tools/liquibase` |
| Data load | `.bat` → `data_loader.py` | `.sh` → `data_loader.py` | `data_loader.py` |
| Object gen/deploy | `.bat` → Python | `.sh` → Python | `bootstrap_generator.py`, `deploy_objects.py` |
| Logs/reports | via Jenkins | via Jenkins | `logger.py`, `generate_report.py` |

## Note on asymmetry

The **Main Jenkinsfile** binds PostgreSQL/MongoDB to the Windows agent and MySQL/MSSQL to the Ubuntu agent, even
though equivalent scripts exist for the other OS. This is a routing decision in `Jenkinsfile`, not a capability
gap.
