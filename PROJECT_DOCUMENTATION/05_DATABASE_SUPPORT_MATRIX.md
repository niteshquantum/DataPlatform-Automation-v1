# 05 — Database Support Matrix

Status legend: **IMPLEMENTED** / **PARTIAL** / **NOT IMPLEMENTED** / **NOT APPLICABLE** / **UNCLEAR**

> Verified by inspecting `jenkins/`, `scripts/batch|bash/`, `liquibase/`, `terraform/`, `objects/`, `requirements/`.

## Summary matrix

| Capability | MySQL | PostgreSQL | MSSQL | MongoDB |
|------------|-------|------------|-------|---------|
| Windows Setup | PARTIAL* | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED |
| Ubuntu Setup | IMPLEMENTED | PARTIAL* | IMPLEMENTED | IMPLEMENTED |
| Schema Deployment (Liquibase) | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | NOT APPLICABLE |
| Data Loading (CSV/JSON) | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED |
| Validation | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED |
| Terraform Provisioning | IMPLEMENTED | IMPLEMENTED | PARTIAL | IMPLEMENTED |
| Liquibase Objects | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | NOT APPLICABLE |
| Objects (custom inputs) | PARTIAL | PARTIAL | PARTIAL | PARTIAL |
| RBAC (gate) | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED |
| Cleanup | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED |
| Main Jenkins routing OS | Ubuntu | Windows | Ubuntu | Windows |

\* PostgreSQL has full scripts on both OS, but the **Main Jenkinsfile** only routes PostgreSQL Setup/Load/Cleanup
to the **Windows** agent (and Ubuntu standalone pipelines exist). MySQL is routed only to **Ubuntu** in the main
pipeline though Windows scripts also exist.

## Per-database detail

### MySQL
- Setup/Load wired in Main Jenkins on **Ubuntu**. Windows scripts present but main pipeline routes MySQL to Ubuntu.
- Liquibase: `liquibase/mysql/master.xml` (placeholder) + generated `master_objects.xml`.
- Objects supported: views, functions, procedures, triggers, events, indexes (`config/common/database_objects.json`).
- Load scripts mirror MSSQL style (`database_inventory`, `table_inventory`, `sql_agent`).

### PostgreSQL
- Most complete implementation. Objects include views, materialized views, functions, procedures, triggers,
  extensions, indexes.
- Config: `config/windows/postgresql.conf`, `config/ubuntu/postgresql.conf` (host 127.0.0.1, port 55432, db
  `DataManagementDB`, user `postgres`, version 17, driver 42.7.3, Liquibase 5.0.3).
- Main Jenkins routes PostgreSQL to **Windows** agent; Ubuntu standalone pipelines also present.

### Microsoft SQL Server (MSSQL)
- Windows: installer-based (`powershell/mssql/install_mssql.ps1`, config-file generation from
  `databases/mssql/templates/ConfigurationFile.template.ini`, `sqlcmd`).
- Ubuntu: Docker/container path (`install_mssql.sh`, `install_mssql_driver.sh`).
- Objects: views, functions, procedures, triggers, indexes.
- Main Jenkins routes MSSQL to **Ubuntu**.

### MongoDB
- Document store. No Liquibase schema (NOT APPLICABLE). Objects = collections + indexes only.
- Windows: Terraform `null_resource` → `powershell/mongodb/install_windows.ps1`; service config + mongosh.
- Ubuntu: `bash/mongodb/setup/install_mongodb.sh`, `start_mongodb.sh`, `configure_mongodb_service.sh`.
- Load via `data_loader_mongodb.py` + `scripts/bash|batch/mongodb/load/load_data.*`.
- Main Jenkins routes MongoDB to **Windows**.

## Object support detail (from `config/common/database_objects.json`)

| Object type | MySQL | PostgreSQL | MSSQL | MongoDB |
|-------------|-------|------------|-------|---------|
| views | yes | yes | yes | no |
| materialized_views | no | yes | no | no |
| functions | yes | yes | yes | no |
| procedures | yes | yes | yes | no |
| triggers | yes | yes | yes | no |
| events | yes | no | no | no |
| indexes | yes | yes | yes | yes |
| extensions | no | yes | no | no |
| collections | no | no | no | yes |

## Asymmetry notes (do not assume symmetry)

- MongoDB has **no RBAC object deployment into the DB** and **no Liquibase** (document model).
- PostgreSQL uniquely supports materialized views and extensions.
- MySQL uniquely supports events.
- The **Main Jenkinsfile is not a full matrix**: it wires only 8 stages (2 DBs × Ubuntu + 2 DBs × Windows).
  Standalone pipelines cover more combinations.
