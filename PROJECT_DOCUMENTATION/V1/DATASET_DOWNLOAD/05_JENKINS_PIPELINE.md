# Jenkins Download Pipeline

## Title
Jenkins Dataset Download Test Pipeline

## Purpose
Documents the Jenkins CI/CD pipeline for testing the Dataset Download module. This pipeline validates the end-to-end download, verification, extraction, and incoming folder verification workflow.

## Scope
Covers the `download_dataset_test.groovy` pipeline definition, its stages, parameters, logging integration, and execution flow.

## Pipeline Location
`download_dataset_test.groovy` (project root)

## Pipeline Parameters

| Parameter | Type | Values | Description |
|-----------|------|--------|-------------|
| `DATABASE` | Choice | `postgresql`, `mysql`, `mongodb`, `mssql` | Target database for dataset |
| `SOURCE_TYPE` | Choice | `google_drive`, `local` | Dataset source type |
| `SOURCE_PATH` | String | Any valid URL or filesystem path | Dataset location |

## Pipeline Architecture

### Stages Overview

```
+-------------------------------------------------------+
|              download_dataset_test.groovy              |
+-------------------------------------------------------+
    |
    +-- Stage 1: Checkout SCM
    |       |
    |       v
    |   git checkout
    |
    +-- Stage 2: Initialize Logging
    |       |
    |       v
    |   logger.py init
    |
    +-- Stage 3: Download Dataset
    |       |
    |       v
    |   download_dataset.bat
    |       |
    |       +-- install_7zip.bat
    |       +-- download_dataset.ps1
    |           +-- download_dataset.py
    |           +-- extract_dataset.py
    |
    +-- Stage 4: Verify Download
    |       |
    |       v
    |   verify_download.py
    |
    +-- Stage 5: Extract Dataset
    |       |
    |       v
    |   extract_dataset.py
    |
    +-- Stage 6: Verify Incoming Folder
    |       |
    |       v
    |   verify_incoming.py
    |
    +-- Post Actions
            |
            +-- Logging finalization
            +-- Artifact archiving
            +-- HTML report publishing
```

## Stage Details

### Stage 1: Checkout SCM
- **Purpose:** Checkout source code from Git repository
- **Implementation:** `checkout scm`
- **Notes:** Standard Jenkins SCM checkout

### Stage 2: Initialize Logging
- **Purpose:** Initialize execution logging for the build
- **Implementation:** Calls `python scripts\logging\logger.py init` with database, action, OS, build number, job name, and build URL
- **Output:** Creates execution log at `logs\{database}\download-test\build_{number}\execution.json`

### Stage 3: Download Dataset
- **Purpose:** Execute the dataset download and extraction workflow
- **Implementation:** Runs `scripts\batch\common\download_dataset.bat` with environment variables:
  - `SOURCE_TYPE={params.SOURCE_TYPE}`
  - `SOURCE_PATH={params.SOURCE_PATH}`
  - `DATABASE={params.DATABASE}`
- **Sub-process:**
  1. `install_7zip.bat` - Ensures 7-Zip is available
  2. `download_dataset.ps1` - Orchestrates download and extraction
  3. `download_dataset.py` - Download logic with skip-if-exists
  4. `extract_dataset.py` - Extraction with state-tracked skip
- **Logging:** Stage start/end tracked via `runTrackedStage` closure

### Stage 4: Verify Download
- **Purpose:** Validate that the dataset was downloaded correctly
- **Implementation:** Runs `python scripts\python\common\verify_download.py` with database, source-type, and source-path arguments
- **Checks:**
  - Archive exists in `incoming/archive/` (for archive datasets)
  - Files exist in `incoming/{database}/` (for non-archive datasets)
  - Reports file size for archives
- **Failure:** Pipeline fails if download verification fails

### Stage 5: Extract Dataset
- **Purpose:** Extract ZIP archive to incoming folder
- **Implementation:** Runs `python scripts\python\common\extract_dataset.py`
- **Behavior:**
  - Skips extraction if already complete (state-tracked)
  - Extracts using Python zipfile or 7-Zip fallback
  - Validates expected folders after extraction
- **Failure:** Pipeline fails if extraction fails or expected folders are missing

### Stage 6: Verify Incoming Folder
- **Purpose:** Validate that the incoming folder has the expected content
- **Implementation:** Runs `python scripts\python\common\verify_incoming.py` with database argument
- **Checks:**
  - For non-archive: files exist in `incoming/{database}/`
  - For archive: folders exist in `incoming/`
- **Failure:** Pipeline fails if incoming folder is empty or missing expected content

## Logging Integration

### Stage Tracking
Each stage uses the `runTrackedStage` closure which wraps stage execution with logging:

```
stage-start -> stageBody -> stage-end (SUCCESS/FAILURE)
```

On failure:
- Logs stage-end with `FAILURE` status
- Calls `logger.py set-error` with failed stage name and message
- Re-raises the exception to halt the pipeline

### Logging Commands
```groovy
python scripts\logging\logger.py init ...
python scripts\logging\logger.py stage-start ...
python scripts\logging\logger.py stage-end ...
python scripts\logging\logger.py set-error ...
python scripts\logging\logger.py finalize ...
```

## Post Actions

### Success
- Echoes `DATASET DOWNLOAD TEST SUCCESSFUL`

### Failure
- Echoes `DATASET DOWNLOAD TEST FAILED`

### Always
- Finalizes logging with current build status
- Archives artifacts:
  - `logs/{database}/{action}/build_{number}/**`
  - `reports/{database}/{action}/build_{number}/**`
  - `reports/history/**`
  - `reports/migration/{database}/**`
- Publishes HTML reports for executive reporting

## Pipeline Configuration

### Concurrency
```groovy
options {
    disableConcurrentBuilds()
}
```
Only one build runs at a time per job.

### Agent
```groovy
agent any
```
Runs on any available Jenkins agent.

## Error Handling

### Stage-Level Error Handling
Each stage is wrapped in a `try/catch` block via `runTrackedStage`:
- **Success path:** Logs `SUCCESS` status
- **Failure path:** Logs `FAILURE` status, sets error info, re-throws exception

### Build-Level Error Handling
- Post `failure` block echoes failure message
- Post `always` block ensures logging finalization even if stages fail

## Usage

### Triggering via Jenkins UI
1. Navigate to the Jenkins job
2. Click "Build with Parameters"
3. Select `DATABASE` (e.g., `postgresql`)
4. Select `SOURCE_TYPE` (e.g., `google_drive`)
5. Enter `SOURCE_PATH` (e.g., Google Drive URL or local path)
6. Click "Build"

### Triggering via Jenkins CLI
```bash
java -jar jenkins-cli.jar -s http://jenkins:8080/ build download_dataset_test \
  -p DATABASE=postgresql \
  -p SOURCE_TYPE=google_drive \
  -p SOURCE_PATH="https://drive.google.com/..."
```

## Artifacts and Reports

### Archived Artifacts
- Execution logs
- Build reports
- Migration reports
- Assessment outputs
- Profiling metadata

### Published Reports
- Executive HTML report for each database migration

## Best Practices
- Always specify `SOURCE_PATH` explicitly to avoid using stale config values
- Use `google_drive` for remote datasets and `local` for development/testing
- Monitor build logs for `[WARNING]` and `[ERROR]` messages
- Check archived artifacts for detailed stage logs on failure
- Ensure Jenkins agent has Python, gdown, and 7-Zip installed

## Known Limitations
- Windows batch commands are used (`bat`), not cross-platform shell commands
- Pipeline is designed for Windows Jenkins agents
- No built-in rollback if download succeeds but extraction fails
- Logging and reporting depend on the `scripts/logging/logger.py` module
