# 12 — Data Loading Architecture

## What happens when you select LOAD

```
dataset (download) -> schema detect -> generate Liquibase XML -> update master.xml
   -> apply Liquibase -> data_loader.py -> validate loaded data
```

## Entry (verified)

`scripts/bash/postgresql/load/load_data.sh` (reused by Windows `load_data.bat`) performs:

1. `start_postgresql.bat` / `validate_postgresql.bat` — ensure DB is up.
2. `download_dataset.bat` → `powershell download_dataset.ps1` → `python download_dataset.py`.
3. `schema_detector.py <db>` — read live schema metadata.
4. `generate_liquibase_xml.py` — build dataset changelog.
5. `update_master_xml.py` — rewrite `master.xml` with includes.
6. `run_liquibase.sh/.bat` — apply schema.
7. `data_loader.py <db>` — load CSV/JSON.
8. `validate_data.py` / `validate_loaded_data.bat`.
9. `deploy_objects.bat` (objects).
10. assessment / reconciliation / discovery engines.

## `data_loader.py` (the core loader)

- Reads `incoming/<db>/*.csv` and `*.json` (note: `incoming/` is **not present** in the repo — it is an
  expected runtime input directory).
- `read_csv_file` tries encodings utf-8-sig, utf-8, cp1252, latin1.
- For each file: derive table name from filename (lowercased, spaces→`_`); detect columns; create table if
  missing; add missing columns via `ALTER TABLE`; batch-insert (`BATCH_SIZE = 500`) via `executemany`.
- **Idempotency:** `LOAD_MODE` env var — `skip` (default, skips already-processed via SHA256 history),
  `force`, `reload` (truncate first).
- On success: move file to `archive/<db>/`, write `metadata/<db>/data_load_history.jsonl`.
- On failure: write `<file>.error.log` to `failed/<db>/`, move file to `failed/<db>/`.

## Database-specific loaders

| DB | Loader | Notes |
|----|--------|-------|
| MySQL | `data_loader.py` + `mysql/load/load_data.py`, `validate_csv.py`, `validate_data.py` | CSV schema test |
| PostgreSQL | `data_loader.py` + `postgresql/load/load_data.py`, `validate_data.py` | |
| MSSQL | `data_loader.py` + `mssql/load/load_data.sh`, `database_inventory.py`, `table_inventory.py`, `sql_agent.py`, `validate_csv.py` | pyodbc, inventory scripts |
| MongoDB | `data_loader_mongodb.py` + `mongodb/load/load_data.*`, `generate_dataset.py`, `load_all.py` | document insert |

## Chunking / transactions

- Inserts in batches of 500 rows; commits per batch. On exception: `conn.rollback()` then file routed to `failed/`.

## Post-load validation

- `validate_loaded_data.bat` / `validate_data.py` re-query row counts / checksums.
- `validate_csv.bat` (MySQL/MSSQL) validates source CSV before load.

## Status

- **IMPLEMENTED** (CSV/JSON, idempotent, archive/failed routing). Not verified at runtime.
- Gap: `incoming/` directory is referenced but absent from the repo — must be supplied at runtime.
