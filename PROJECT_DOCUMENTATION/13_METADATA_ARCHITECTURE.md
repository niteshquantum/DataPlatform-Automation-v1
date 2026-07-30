# 13 — Metadata Architecture

## What metadata exists

`metadata/` is the **machine-written knowledge store** produced by the Python engines at runtime. The repo
ships only empty per-DB folders (`.gitkeep`); content is generated during runs.

| Subtree | Produced by | Contents |
|----------|--------------|-----------|
| `metadata/<db>/data_load_history.jsonl` | `data_loader.py` | per-file SHA256 + row counts + status |
| `metadata/<db>/profiling/` | `profiling/data_profiler.py` | column-level statistics |
| `metadata/<db>/discovery/` | `discovery/discovery_engine.py`, `growth_analyzer.py`, `requirement_analyzer.py` | env discovery, growth trends, requirements |
| `metadata/<db>/assessment/` | `assessment/assessment_engine.py` | complexity/readiness/risk scores |
| `metadata/<db>/reconciliation/` | `reconciliation/reconciliation_engine.py` | source vs target reconciliation |
| `metadata/<db>/recommendation/` | `recommendation/recommendation_engine.py` | recommended actions |
| `metadata/<db>/governance/` | `governance/action_plan_engine.py` | governance action plan |
| `metadata/liquibase_execution_history.jsonl` | (legacy `run_liquibase.py`) | not produced by active pipelines |

## Who creates it

The Python engines invoked near the end of a LOAD pipeline (after data load + object deploy):
- `run_data_profiling.bat/.sh`
- `run_assessment.bat all`
- `run_reconciliation.bat <db>`
- `discovery_engine.py`, `growth_analyzer.py`, `requirement_analyzer.py`
- `run_recommendation.bat`, `run_action_plan.bat`
- migration report builders (`executive_report.py`, `technical_report.py`)

## Who reads it

- `generate_assessment_report.bat` → `assessment_report.py`
- migration `generate_executive_report.bat` / `generate_technical_report.bat` → `reporting/migration/*`
- The Jenkins `archiveArtifacts` step captures `metadata/<area>/<db>/**` as build artifacts.
- `outputs/assessments/<db>/` holds assessment outputs (archived by Jenkins).

## Why it is needed

Metadata connects **datasets → schema → objects → assessment → migration planning**. It turns a raw load into
auditable, queryable evidence used by reporting and the migration analytics suite.

## Status

- Folders scaffolded: **IMPLEMENTED** (empty placeholders).
- Engines that produce it: **IMPLEMENTED** (verified by file presence + Jenkins wiring).
- Not verified at runtime (no execution performed).
