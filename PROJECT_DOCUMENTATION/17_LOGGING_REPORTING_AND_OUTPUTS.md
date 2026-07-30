# 17 — Logging, Reporting, and Outputs

## What is generated and where it goes

| Artifact | Location | Class |
|----------|----------|--------|
| Execution log (JSON) | `logs/<db>/<action>/build_<N>/execution.json` | GENERATED |
| HTML report | `reports/<db>/<action>/build_<N>/report.html` | REPORT |
| JSON report | `reports/<db>/<action>/build_<N>/report.json` | REPORT |
| Build history | `reports/history/**` | REPORT |
| Migration reports | `reports/migration/<db>/executive_report.html`, `technical_report.html` | REPORT |
| Assessment outputs | `outputs/assessments/<db>/**`, `outputs/assessments/assessment_report.json` | GENERATED |
| Metadata | `metadata/<area>/<db>/**` | GENERATED |
| Loaded/archive data | `archive/<db>/` (data loader moves processed files) | OUTPUT |
| Failed data | `failed/<db>/*.error.log` + moved files | FAILURE OUTPUT |
| Liquibase objects | `liquibase/<db>/objects/`, `master_objects.xml` (runtime) | GENERATED |
| Generated object SQL | `objects/<db>/generated/` (runtime) | GENERATED |

## Logging mechanism (verified)

- `scripts/logging/logger.py` is a CLI with subcommands: `init`, `set-environment`, `stage-start`,
  `stage-end`, `set-error`, `finalize`.
- Writes a structured `execution.json` (pipeline metadata, stages[], environment, error).
- Called by `executePipeline` (main Jenkins) and `runTrackedStage` (standalone) around every stage.
- **Direct-local `.bat`/`.sh` pipelines do NOT call logger.py** — they only print to console.

## Reporting mechanism (verified)

- `generate_report.py --database --action --build-number` reads `execution.json` and emits `report.json`
  + styled `report.html` (stage table, environment, error section).
- `generate_history.py` appends build summary to `reports/history/`.
- `archiveArtifacts` in Jenkins captures logs/reports/metadata/outputs as build artifacts.

## `failed/` meaning

- The data loader writes `<filename>.error.log` and moves failing CSV/JSON into `failed/<db>/`.
- Cleanup pipelines also use `failed/` for cleanup error artifacts.
- In the repo, `failed/` contains only `.gitkeep` (populated at runtime).

## `outputs/` meaning

- `outputs/assessments/<db>/` holds assessment engine results archived by Jenkins.
- In the repo, only `.gitkeep` placeholders exist.

## Status

- Logging + reporting: **IMPLEMENTED** (Jenkins modes). **NOT CONNECTED** in direct-local mode.
- Output directories scaffolded: **IMPLEMENTED** (empty placeholders).
- Not verified at runtime.
