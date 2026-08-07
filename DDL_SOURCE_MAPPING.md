# DDL Source Mapping (Architecture Verification — Phase 2)

Runtime artifacts are mapped back to the source code that produces and consumes them.
Scope is strictly limited to the 7 inspected files.

| Artifact | Producer | Consumer | Next Stage |
|---|---|---|---|
| schema_registry.json | `scripts/schema_detector.py` (lines 194-199, 207-208, 173-174, 256) | `scripts/python/mysql/setup/generate_liquibase_xml.py` (lines 7, 12-13); also read/reconciled by `scripts/python/common/objects/bootstrap_generator.py` (lines 127-205, 218-223) | Drives Liquibase changeset generation (columns → createTable / addColumn) |
| schema_status.json | `scripts/python/mysql/setup/generate_liquibase_xml.py` (lines 148, 152-159) — writes `{ "schema_changed": <bool> }` to `metadata/mysql/schema_status.json` | Not consumed by any of the 7 inspected files (external pipeline decision point) | Gates whether object-generation / deployment pipelines proceed |
| master.xml | `scripts/python/mysql/setup/update_master_xml.py` (lines 8, 14-28, 63-67) — creates/rewrites `liquibase/mysql/master.xml` from all sibling `*.xml` | Liquibase runtime via `scripts/batch|bash/mysql/setup/run_liquibase.*` (external to inspected files) | Liquibase executes schema changesets against the target DB |
| master_objects.xml | `scripts/python/common/objects/generate_master_objects.py` (lines 28-107) — writes `liquibase/<db>/master_objects.xml` | `scripts/python/common/objects/deploy_objects.py` (lines 38-43, 45-48) — reads it as the changelog argument | Liquibase deployment of DB objects |
| generated SQL objects | `scripts/python/common/objects/bootstrap_generator.py` (lines 266, 287-313) — orchestrates generators into `objects/<db>/generated/` | `scripts/python/common/objects/generate_liquibase_objects.py` (lines 21-57) — wraps SQL into Liquibase XML via `xml_generators/*.py` | Liquibase XML generation (SQL → Liquibase changesets) |
| generated Liquibase XML | `scripts/python/common/objects/generate_liquibase_objects.py` (lines 21-57) — writes into `liquibase/<db>/objects/generated/` | `scripts/python/common/objects/generate_master_objects.py` (lines 47-92) — includes files in `master_objects.xml` | Assembly into `master_objects.xml` then deployment |
| data_load_history.jsonl | Not referenced by any of the 7 inspected files | Not referenced by any of the 7 inspected files | Not determinable from inspected scope |

## Flow

CSV / JSON
↓
schema_detector.py
↓
schema_registry.json
↓
generate_liquibase_xml.py
↓
schema_status.json
↓
update_master_xml.py
↓
master.xml
↓
Liquibase

bootstrap_generator.py
↓
generated SQL objects
↓
generate_liquibase_objects.py
↓
generated Liquibase XML
↓
generate_master_objects.py
↓
master_objects.xml
↓
deploy_objects.py
↓
Liquibase

Note: `data_load_history.jsonl` is not referenced within the 7 inspected files, so it has no mapping here.
