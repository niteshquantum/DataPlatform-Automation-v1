# 06 — Configuration Architecture

## How the automation knows what to connect to

Every script answers "which database, host, port, credentials, driver, Liquibase version, dataset?" from
**`.conf` files under `config/`**, resolved by **operating system** and **database name**.

### Config file layout

```
config/
  common/
    database_objects.json     # which object types each DB supports
    dataset.conf              # dataset location/name
    objects.conf              # object-generation toggles
  windows/
    mysql.conf  mssql.conf  mssql_media.conf  mongodb.conf  postgresql.conf
  ubuntu/
    mysql.conf  mssql.conf  mongodb.conf  postgresql.conf
```

### Resolution rules (verified)

- Python uses `scripts/python/common/config_loader.py`:
  - `load_database_config(name)` → if `platform.system() == "Windows"` reads
    `config/windows/<name>.conf`, else `config/ubuntu/<name>.conf`.
  - `get_project_root()` = three parents above `config_loader.py` (repo root).
- Batch scripts source `scripts/batch/common/set_project_root.bat` (computes `PROJECT_ROOT` as `..\..\..` from the
  script, validates `config/` exists), then parse the `.conf` line-by-line with `for /f "tokens=1,* delims=="`.
- Bash scripts source `scripts/bash/common/set_project_root.sh` (realpath of `../../..`).

### Example: `config/windows/postgresql.conf`

```
POSTGRESQL_HOST=127.0.0.1
POSTGRESQL_PORT=55432
POSTGRESQL_DB=DataManagementDB
POSTGRESQL_USER=postgres
POSTGRESQL_PASSWORD=root1234
POSTGRESQL_VERSION=17
POSTGRESQL_DRIVER_VERSION=42.7.3
LIQUIBASE_VERSION=5.0.3
```

These keys are read by `run_liquibase.bat` (driver jar path `tools/drivers/postgresql-<ver>.jar`),
`deploy_postgresql.bat`, and the Python `data_loader` / connection modules.

### Common config

- `config/common/database_objects.json` — capability matrix consumed by
  `scripts/python/common/objects/database_capabilities.py` to decide which object generators run.
- `config/common/dataset.conf` — dataset name/location referenced by `download_dataset.py`.
- `config/common/objects.conf` — object-generation settings.

### Environment variables

- `PROJECT_ROOT` — set by every batch/bash entry wrapper; used by child scripts.
- `PYTHONPATH` — set to `PROJECT_ROOT` in load/object scripts so `scripts.python.*` imports resolve.
- `LOAD_MODE` — `skip` (default, idempotent), `force`, `reload` (truncate) consumed by `data_loader.py`.
- `CLEANUP_MODE` — `PRESERVE_DATA` / `DELETE_DATA`, passed from Jenkins params into cleanup pipelines.
- Jenkins build vars `BUILD_NUMBER`, `JOB_NAME`, `BUILD_URL` — used by `logger.py`.

### Secrets handling (CURRENT BEHAVIOR)

- **Plaintext credentials** live in `config/<os>/<db>.conf` (e.g. `POSTGRESQL_PASSWORD=root1234`).
- RBAC credentials live in `rbac/credentials.json` as **SHA256 hashes** (not plaintext); verified in
  `rbac/utils.verify_password`.
- RBAC `USERNAME`/`PASSWORD` are passed as Jenkins build parameters (password type) into `auth_cli.py`/`cli.py`.
- Liquibase is invoked with `--password=<value>` on the command line (visible in process args / logs).

> RISK: Database passwords are stored in plaintext config and echoed into Liquibase command lines. This is fine for
> a local lab but must be replaced with a secrets manager / Jenkins credentials for any shared environment.

### Path / project-root resolution

- All scripts anchor on `PROJECT_ROOT` derived from the calling script's location, never on CWD assumptions alone.
- `set_project_root.bat` explicitly fails if `config/` is not found under the computed root.

### Database capabilities

- `database_capabilities.py` loads `config/common/database_objects.json` into a `DatabaseCapabilities` object.
- `supports_object(db, type)` is the single source of truth used by both `generate_liquibase_objects.py` and
  `bootstrap_generator.py` to gate which object generators execute.
