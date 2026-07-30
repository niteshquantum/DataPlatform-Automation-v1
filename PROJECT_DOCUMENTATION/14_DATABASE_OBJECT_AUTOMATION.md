# 14 — Database Object Automation

## What it solves

Databases need more than tables: views, procedures, functions, triggers, indexes, events, materialized views,
extensions. Hand-writing and deploying these per database is repetitive and error-prone. This subsystem
**detects available schema metadata, generates object SQL + Liquibase XML changesets, and deploys them
through the same Liquibase runner used for schema** — keeping objects versioned and repeatable.

## Support matrix (from `config/common/database_objects.json`)

| Object | MySQL | PostgreSQL | MSSQL | MongoDB |
|--------|-------|------------|-------|---------|
| views | yes | yes | yes | no |
| materialized_views | no | yes | no | no |
| functions | yes | yes | yes | no |
| procedures | yes | yes | yes | no |
| triggers | yes | yes | yes | no |
| events | yes | no | no | no |
| indexes | yes | yes | yes | yes |
| extensions | no | yes | no | no |
| collections | no | no | no | yes |

## Flow (verified)

```
deploy_objects.bat
  -> check_schema_changed.py        (MISSING - see status)
  -> bootstrap_generator.py <db>      (GENERATION ONLY)
       -> ObjectDetector(database).detect()
       -> generate_views/functions/procedures/triggers/events/indexes/...  (SQL in objects/<db>/generated)
       -> generate_liquibase_objects.py  (XML changesets in liquibase/<db>/objects)
       -> generate_master_objects.py    (builds liquibase/<db>/master_objects.xml)
  -> deploy_objects.py <db>           (DEPLOY via Liquibase)
       -> subprocess run_liquibase.bat|sh master_objects.xml
  -> validate_objects.bat
```

## Key files (actual)

| File | Role |
|------|------|
| `scripts/python/common/objects/database_capabilities.py` | `supports_object(db,type)` source of truth |
| `scripts/python/common/objects/object_detector.py` | detect schema metadata |
| `scripts/python/common/objects/bootstrap_generator.py` | orchestrates generation (no deploy) |
| `scripts/python/common/objects/generate_liquibase_objects.py` | dispatch per-object XML generators |
| `scripts/python/common/objects/xml_generators/*` | per-type XML changeset generators |
| `scripts/python/common/objects/generators/*` | per-type SQL generators |
| `scripts/python/common/objects/generate_master_objects.py` | build `master_objects.xml` from templates |
| `scripts/python/common/objects/deploy_objects.py` | deploy via DB/OS Liquibase runner |
| `scripts/python/common/objects/validate_objects.py` | post-deploy validation |
| `objects/<db>/custom/<type>/` | drop-zone for custom object inputs (mostly empty placeholders) |

## Generation vs deployment separation

`bootstrap_generator.py` only **generates** (cleans stale `generated/` + `liquibase/<db>/objects/`,
detects, generates SQL + XML + master). `deploy_objects.py` **deploys** via Liquibase. This prevents
Liquibase from running twice. The `.bat` wrapper sequences: generate → deploy → validate.

## Status

- Generation + Liquibase deployment: **IMPLEMENTED**.
- Custom object input folders: **PARTIAL** (empty placeholders; no sample objects committed).
- `deploy_objects.bat` line 25 calls `check_schema_changed.py`, which **does not exist** in the repo
  (verified). In direct-local mode this would error before generation; Jenkins standalone mode skips this
  wrapper (it calls `bootstrap_generator.py` directly via its own stages). Marked as a defect in status doc.
- Not verified at runtime.
