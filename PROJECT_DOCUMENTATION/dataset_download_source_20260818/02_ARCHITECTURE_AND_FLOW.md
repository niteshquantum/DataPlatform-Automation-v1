# Architecture and Flow

## A. Standalone / Direct Pipeline Flow

```
CI_CD/<database>/<os>/load_pipeline.groovy
    ↓
stage('Download Dataset')
    ↓
runTrackedStage
    ↓
withEnv([SOURCE_TYPE, SOURCE_PATH, FORCE_DOWNLOAD])
    ↓
download_dataset.bat / download_dataset.sh
    ↓
download_dataset.ps1 (Windows only)
    ↓
download_dataset.py
    ↓
source_utils.get_output_filename()
    ↓
downloader_factory.get_downloader()
    ↓
google_drive.py OR local.py
    ↓
validate_archive()
    ↓
state update
    ↓
extract_dataset.py (optional)
    ↓
stage('Verify Download')
    ↓
verify_download.py
```

The standalone pipelines (`CI_CD/mysql/windows/load_pipeline.groovy`, `CI_CD/mysql/ubuntu/load_pipeline.groovy`, etc.) were used for integration testing. They contain the full pipeline definition including database setup, download, extraction, loading, and assessment.

## B. Master Routed Jenkins Flow

```
jenkins/Jenkinsfile
    ↓
parameters: DATABASE, ACTION, SOURCE_TYPE, SOURCE_PATH, FORCE_DOWNLOAD, ...
    ↓
Resolve Pipeline Route
    ↓
pipeline_config.groovy  (routing only — node/OS/path)
    ↓
jenkins/common/<database>/load_steps.groovy
    ↓
stage('Download Dataset')
    ↓
runTrackedStage + withEnv([SOURCE_TYPE, SOURCE_PATH, FORCE_DOWNLOAD])
    ↓
download_dataset.bat / download_dataset.sh
    ↓
download_dataset.py
    ↓
[rest of download/validate/extract/verify flow]
    ↓
remaining database pipeline stages
```

### Critical Distinction

The **standalone** CI/CD pipelines are:
- `CI_CD/mysql/windows/load_pipeline.groovy`
- `CI_CD/mysql/ubuntu/load_pipeline.groovy`
- `CI_CD/postgresql/windows/load_pipeline.groovy`
- `CI_CD/mssql/windows/load_pipeline.groovy`
- `CI_CD/mongodb/windows/load_pipeline.groovy`

These were used for **testing only**.

The **production master routing** modules are:
- `jenkins/common/mysql/load_steps.groovy`
- `jenkins/common/postgresql/load_steps.groovy`
- `jenkins/common/mongodb/load_steps.groovy`
- `jenkins/common/mssql/load_steps.groovy`

These are loaded dynamically by `jenkins/Jenkinsfile` via `load env.ROUTED_PIPELINE`.

### Parameter Propagation Path

1. `jenkins/Jenkinsfile` defines `SOURCE_TYPE`, `SOURCE_PATH`, `FORCE_DOWNLOAD` parameters
2. Context map includes `sourceType: params.SOURCE_TYPE`, `sourcePath: params.SOURCE_PATH`, `forceDownload: params.FORCE_DOWNLOAD`
3. `jenkins/common/<database>/load_steps.groovy` receives context via `module.execute(context)`
4. Download Dataset stage uses `withEnv(["SOURCE_TYPE=${context.sourceType}", ...])`
5. `download_dataset.bat` or `download_dataset.sh` reads environment variables
6. `download_dataset.py` reads `os.getenv("SOURCE_TYPE")` etc.

## Files NOT Modified for Routing
- `jenkins/pipeline_config.groovy` — routing only
- `jenkins/common/common_stage_tracker.groovy` — logging/tracking only
