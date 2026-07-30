# 18 — Dependencies and Prerequisites

## Tool matrix

| Tool | Purpose | Version (config) | Windows | Ubuntu | Install method | Used by |
|------|---------|------------------|---------|--------|-----------------|----------|
| Python | Core automation logic | (runtime validated, not pinned) | yes | yes | `install_python_requirements.bat/.sh` (pip) | all engines |
| Java | Liquibase runtime | (validated) | yes | yes | `validate_java_runtime` | Liquibase |
| Terraform | Local DB provisioning (null provider) | `>= 1.13.0` | yes | yes | `install_terraform.bat/.sh` → `tools/terraform/` | `deploy_*.bat/.sh` |
| Liquibase | Schema/object migration | 5.0.3 (postgresql.conf) | yes | yes | `install_liquibase.bat/.sh` → `tools/liquibase/` | `run_liquibase.*` |
| JDBC drivers | DB connectivity | pg 42.7.3 (conf) | yes | yes | `install_*_driver.bat/.ps1/.sh` → `tools/drivers/` | Liquibase |
| DB binaries | MySQL/PG/MSSQL/Mongo | per conf | yes | yes | Terraform→PowerShell/Bash | setup |
| Python libs | mysql.connector, psycopg2, pyodbc, etc. | `requirements/*.txt` | yes | yes | pip | loaders |
| sqlcmd | MSSQL CLI | (validated) | yes | yes | `install_sqlcmd.bat` | mssql queries |
| mongosh | MongoDB shell | (validated) | yes | yes | `install_mongosh` | mongodb |

## Requirements files

- `requirements/common.txt` — shared Python packages.
- `requirements/mysql.txt`, `postgresql.txt`, `mssql.txt`, `mongodb.txt` — per-DB extras.
- Installed by `install_python_requirements.bat/.sh` which call pip against these files.

## Tools directory (runtime)

`tools/` ships as empty placeholders: `tools/liquibase/`, `tools/terraform/`, `tools/drivers/`.
Install scripts populate them. Pipelines **fail fast** if `tools/terraform/terraform[.exe]` or
`tools/liquibase/liquibase[.bat]` are missing.

## Role summary

- **Python** — the cross-OS brain (config, loaders, generators, discovery, reporting).
- **Java** — runs Liquibase.
- **Terraform** — orchestrates local DB install/start via `local-exec`.
- **Liquibase** — applies schema + object changelogs.
- **Jenkins** — CI/CD orchestrator + RBAC + reporting (Modes 1 & 2).
- **DB drivers (JDBC/ODBC)** — connectivity for Liquibase and Python loaders.
- **DB binaries** — the actual database engines installed locally.

## Status

- Dependency structure: **IMPLEMENTED** (install/validate scripts present per OS/DB).
- Versions are **not globally pinned** except Terraform (`>=1.13.0`) and Liquibase/driver in `.conf`.
- Not verified at runtime (no installs executed).
