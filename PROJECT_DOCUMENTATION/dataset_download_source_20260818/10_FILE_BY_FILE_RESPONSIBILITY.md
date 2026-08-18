# File by File Responsibility

## Master Jenkins Files

| File | Responsibility | Change |
|------|----------------|--------|
| `jenkins/Jenkinsfile` | Master pipeline definition, parameter declaration, context building, routed pipeline execution | Added `SOURCE_TYPE`, `SOURCE_PATH`, `FORCE_DOWNLOAD` parameters. Added `sourceType`, `sourcePath`, `forceDownload` to context map. |
| `jenkins/pipeline_config.groovy` | Routing configuration — maps DATABASE+ACTION to node/OS/path | **NO CHANGE** — routing only |
| `jenkins/common/common_stage_tracker.groovy` | Stage logging wrapper (stage-start, stage-end, set-error) | **NO CHANGE** — logging only |
| `jenkins/common/mysql/load_steps.groovy` | MySQL load pipeline stages | Added `withEnv` to Download Dataset. Verify Download already existed. |
| `jenkins/common/postgresql/load_steps.groovy` | PostgreSQL load pipeline stages | Added `withEnv` to Download Dataset. Added Verify Download stage. |
| `jenkins/common/mongodb/load_steps.groovy` | MongoDB load pipeline stages | Added `withEnv` to Download Dataset. Added Verify Download stage. |
| `jenkins/common/mssql/load_steps.groovy` | MSSQL load pipeline stages | Added `withEnv` to Download Dataset. Verify Download already existed. |

## Standalone CI/CD Test Pipelines

| File | Change |
|------|--------|
| `CI_CD/mysql/windows/load_pipeline.groovy` | Added parameters, withEnv, Verify Download; removed SCHEMA_SOURCE |
| `CI_CD/mysql/ubuntu/load_pipeline.groovy` | Added FORCE_DOWNLOAD parameter and withEnv; removed SCHEMA_SOURCE |
| `CI_CD/postgresql/windows/load_pipeline.groovy` | Added parameters, withEnv, Verify Download |
| `CI_CD/mssql/windows/load_pipeline.groovy` | Added parameters, withEnv, Verify Download |
| `CI_CD/mongodb/windows/load_pipeline.groovy` | Added parameters, withEnv, Verify Download |

## Python Source Files

| File | Responsibility | Change |
|------|----------------|--------|
| `scripts/python/common/source_utils.py` | Output filename resolution, archive detection | Local ZIP now returns `config["DATASET_NAME"]` instead of `Path(source_path).name` |
| `scripts/python/common/download_dataset.py` | Download orchestration, validation, state update | Added structured logging markers; preserved atomic temp→validate→replace |
| `scripts/python/common/archive_utils.py` | ZIP validation, 7-Zip fallback, folder listing | Added `.csv`/`.json` content validation for both zipfile and 7-Zip paths |
| `scripts/python/common/extract_dataset.py` | Extraction, merge, cleanup, state update | Removed duplicate EXTRACTION START/SUCCESS markers; preserved cleanup and state logic |
| `scripts/python/common/dataset_state.py` | State tracking (download + extraction) | **NO CHANGE** |
| `scripts/python/common/verify_download.py` | Post-download verification | **NO CHANGE** |
| `scripts/python/common/verify_incoming.py` | Post-extraction verification | **NO CHANGE** |
| `scripts/python/common/downloaders/local.py` | Local file/folder copy | **NO CHANGE** |
| `scripts/python/common/downloaders/google_drive.py` | Google Drive download | **NO CHANGE** |
| `scripts/python/common/factory/downloader_factory.py` | Downloader registry | **NO CHANGE** |

## Entry Point Files

| File | Responsibility | Change |
|------|----------------|--------|
| `scripts/batch/common/download_dataset.bat` | Windows batch entry point | **NO CHANGE** |
| `scripts/powershell/common/download_dataset.ps1` | Windows PowerShell wrapper | **NO CHANGE** |
| `scripts/bash/common/download_dataset.sh` | Ubuntu bash entry point | **NO CHANGE** |

## Configuration

| File | Responsibility | Change |
|------|----------------|--------|
| `config/common/dataset.conf` | Primary dataset configuration | **NO CHANGE** — env vars override config values |
