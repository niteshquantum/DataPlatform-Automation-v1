# 22 — Troubleshooting Guide

> Safe, static-analysis-based guidance. No destructive commands are suggested.

## Likely issues

| Symptom | Cause | Verify | Safe resolution |
|---------|-------|---------|------------------|
| `ERROR: PROJECT ROOT INITIALIZATION FAILED` | Script run from wrong dir; `config/` not found | `cd` to repo root; check `set_project_root.bat` | Run from repo root; ensure `config/` exists |
| `python` / `java` not recognized | Runtime not on PATH | `validate_python_runtime`, `validate_java_runtime` | Install Python3/Java; re-run validate scripts |
| `Terraform not found` / `terraform.exe` missing | `tools/terraform/` empty | `Test-Path tools/terraform/terraform.exe` | Run `install_terraform.bat/.sh` first |
| `LIQUIBASE EXECUTABLE NOT FOUND` | `tools/liquibase/` empty | check `tools/liquibase/liquibase.bat` | Run `install_liquibase.bat/.sh` |
| `POSTGRESQL JDBC DRIVER NOT FOUND` | driver jar missing/version mismatch | check `tools/drivers/postgresql-<ver>.jar` vs `POSTGRESQL_DRIVER_VERSION` in `.conf` | Install correct driver version |
| Port conflict on 55432 / 1433 / 3306 | DB already running / port in use | `validate_port.bat` / `validate_port.py` | Stop existing instance; or change port in `.conf` |
| `data_loader` finds no files | `incoming/<db>/` missing/empty | check `incoming/<db>/*.csv` | Populate `incoming/<db>/` before LOAD |
| Liquibase lock stuck | Previous run interrupted | inspect `DATABASECHANGELOGLOCK` | Investigate lock row; do NOT force-drop in shared env |
| `deploy_objects` errors immediately | `check_schema_changed.py` absent | `Get-ChildItem check_schema_changed.py` | Call `bootstrap_generator.py` + `deploy_objects.py` directly; or add the missing script |
| RBAC `ACCESS_DENIED` | Role lacks `<db>.<action>` | check `rbac/roles.json` | Grant permission to role or use correct credentials |
| RBAC `AUTHENTICATION_FAILED` | Wrong password / disabled user | check `rbac/credentials.json` (SHA256) | Re-hash password with `rbac/utils.hash_password` |
| Jenkins stage skipped on build #1 | `when { currentBuild.number > 1 }` | first build only registers params | Run the build a second time with chosen params |
| Windows service config skipped | Not running as Administrator | `check_admin_privileges.bat` returns non-0 | Run agent as admin, or accept project-local mode |
| Objects not created | `master_objects.xml` not generated | check `liquibase/<db>/master_objects.xml` | Run `bootstrap_generator.py <db>` then `deploy_objects.py <db>` |
| MongoDB steps differ | Mongo has no Liquibase/objects | expected; collections/indexes only | Use mongo-native scripts |

## Notes

- The active Liquibase runner is `run_liquibase.bat/.sh`, **not** `scripts/run_liquibase.py` (legacy/unused).
- All `.bat` pipelines abort on first `errorlevel 1`; read the last printed step to locate the failure.
- Jenkins `executePipeline` always finalizes `logger.py` + `generate_report.py` even on failure — check
  `reports/<db>/<action>/build_<N>/report.html` for the failed stage.
