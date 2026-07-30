# 16 — Validation Framework

Validators are scattered across the OS-layer scripts and Python engines. Classified by purpose:

| Class | Script(s) | Input | Checks | Pass criteria | Failure behavior | Called from |
|-------|----------|-------|---------|----------------|---------------------|--------------|
| Runtime (Python) | `common/validate_python_runtime.bat/.sh` → `python` | interpreter | Python present | version prints | exit 1, pipeline aborts | all pipelines |
| Runtime (Java) | `common/validate_java_runtime.bat/.sh` | `java -version` | Java present | version prints | exit 1 | setup/liquibase |
| Tools | `*/install_tools.bat`, `*/validate_tools.bat`, `common/validate_tools.sh` | installed bins | required tools present | all found | exit 1 | setup |
| Driver | `*/validate_postgresql_driver.bat`, `validate_mssql_driver.bat`, `validate_liquibase.bat` | jars/bins | JDBC driver + Liquibase exist | present | exit 1 | before liquibase |
| Environment | `*/validate_environment.bat` | config + services | DB reachable/config valid | checks pass | exit 1 | end of setup |
| DB-specific | `validate_mysql.bat`, `validate_postgresql.bat`, `validate_mssql.bat` | live DB connection | connect + basic query | success | exit 1 | load/setup |
| Port | `*/validate_port.bat`, `validate_port.py` | config port | port free / listening | as expected | exit 1 | setup |
| Schema | `schema_detector.py` | live schema | readable metadata | ok | raises | load |
| Dataset | `validate_csv.bat`, `validate_csv.py` | CSV files | columns/encoding | ok | exit 1 | load (mysql/mssql) |
| Data (post-load) | `validate_data.py`, `validate_loaded_data.bat/.sh` | loaded tables | row counts / checksums | match | exit 1 | load |
| Objects | `validate_objects.bat`, `validate_objects.py` | deployed objects | objects exist | pass | exit 1 | objects |
| Cleanup | `*/validate_cleanup.bat/.ps1` | post-cleanup state | resources removed | pass | warn | cleanup |
| Admin | `check_admin_privileges.bat` | Windows token | admin rights | 0/non-0 | branches mode | setup |

## How we know automation succeeded

1. Each phase script returns a non-zero exit code on failure; the `.bat`/`runTrackedStage` chain aborts.
2. `logger.py` records per-stage `status` (SUCCESS/FAILURE) and a `final_status` in `logs/<db>/<action>/build_N/execution.json`.
3. `generate_report.py` renders `reports/.../report.html` with stage table + error section.
4. Post-load validators confirm row counts; post-object validators confirm object presence.

## Status

- Validators present across all phases: **IMPLEMENTED**.
- Not verified at runtime (no execution performed).
- Note: standalone/local pipelines rely on script exit codes; the detailed `logger.py` stage tracking is
  fully active only in Jenkins modes.
