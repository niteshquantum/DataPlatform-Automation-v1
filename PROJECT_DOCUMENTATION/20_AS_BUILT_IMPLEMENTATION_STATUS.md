# 20 — As-Built Implementation Status

> Honest status from static inspection. No runtime execution was performed.

## Capability status matrix

| Capability | Status | Evidence / Note |
|------------|--------|----------------------|
| Main Jenkins pipeline (Mode 1) | IMPLEMENTED | `jenkins/Jenkinsfile`, routes DB→OS via agent labels |
| Standalone Jenkins pipelines (Mode 2) | IMPLEMENTED | 24 `.groovy` pipelines across DB/OS |
| Direct local `.bat`/`.sh` (Mode 3) | IMPLEMENTED | `scripts/batch|bash/<db>/*_pipeline.*` |
| Three modes share core automation | VERIFIED | All call `scripts/batch|bash/<db>/...` |
| Terraform local provisioning | IMPLEMENTED | `terraform/*/main.tf` null_resource local-exec |
| Liquibase schema deployment (runners) | IMPLEMENTED | `run_liquibase.bat/.sh` |
| Liquibase runtime-generated changelogs | IMPLEMENTED | `update_master_xml.py`, `generate_liquibase_xml.py` |
| Data loading (CSV/JSON) | IMPLEMENTED | `data_loader.py`, idempotent, archive/failed routing |
| Database object generation | IMPLEMENTED | `bootstrap_generator.py` + generators |
| Database object deployment (Liquibase) | IMPLEMENTED | `deploy_objects.py` → `run_liquibase` |
| RBAC authentication/authorization | IMPLEMENTED | `auth.py`, `cli.py`, JSON store |
| RBAC applied in Main Jenkins | IMPLEMENTED | `executePipeline` |
| RBAC applied in standalone/local | NOT CONNECTED | standalone `.groovy` & local `.bat` skip RBAC |
| Logging (logger.py) | IMPLEMENTED | active in Jenkins modes |
| Logging in direct-local mode | NOT CONNECTED | local pipelines don't call logger.py |
| Reporting (HTML/JSON) | IMPLEMENTED | `generate_report.py`, `generate_history.py` |
| Validation framework | IMPLEMENTED | runtime/env/schema/data/object validators |
| Discovery/Assessment/Reconciliation/Recommendation | IMPLEMENTED | engines present + Jenkins-wired |
| Metadata store | PARTIAL | folders scaffolded; engines generate at runtime |
| Custom object input folders | PARTIAL | empty placeholders (`.gitkeep`) |
| `tools/` binaries (liquibase/terraform/drivers) | NOT PRESENT | empty placeholders; installed at runtime |
| `incoming/` dataset directory | NOT PRESENT | referenced by `data_loader.py`; expected runtime input |

## Defects / gaps (must not be claimed as working)

| Item | Status | Impact |
|------|--------|--------|
| `deploy_objects.bat` calls `check_schema_changed.py` | BROKEN | File absent in repo; direct-local object deploy errors before generation |
| `scripts/run_liquibase.py` (legacy) | LEGACY / UNUSED | Hardcodes MySQL, scans non-existent `liquibase/generated/`; not used by pipelines |
| Committed `liquibase/<db>/master.xml` | PLACEHOLDER | Empty; real changelogs generated at runtime |
| Plaintext DB passwords in `config/*.conf` | CURRENT BEHAVIOR (RISK) | Fine for local lab; unsafe for shared env |
| RBAC password passed on CLI | CURRENT BEHAVIOR (RISK) | Visible in Jenkins console / process args |
| Main Jenkins DB→OS matrix | PARTIAL | Only 8 stages wired (MySQL/MSSQL→Ubuntu, Mongo/PG→Windows) |
| MongoDB Liquibase/Objects | NOT APPLICABLE | document store; collections/indexes only |

## Classification legend

- IMPLEMENTED — code present and wired.
- PARTIAL — present but incomplete.
- PLACEHOLDER — scaffold only.
- LEGACY / UNUSED — exists, not part of active flow.
- NOT CONNECTED — capability exists elsewhere but not wired here.
- NOT APPLICABLE — not relevant for the DB type.
- UNKNOWN — could not verify from static inspection.

## Bottom line

The platform is a **functional, well-structured automation framework** with a verified three-mode entry design
over a shared core. The most material real gaps are: (1) a missing `check_schema_changed.py` that breaks
local object deployment, (2) unused legacy `run_liquibase.py`, (3) RBAC/reporting not wired into local mode,
and (4) runtime-only inputs (`tools/`, `incoming/`) that must be supplied before a run.
