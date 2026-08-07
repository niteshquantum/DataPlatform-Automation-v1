# Dataset Download Module

## Title
Dataset Download Module - V1 Documentation

## Purpose
Provides automated dataset acquisition, validation, extraction, and verification capabilities for database migration pipelines. Supports two source types: Google Drive and local filesystem. Designed for Windows environments with Jenkins CI/CD integration.

## Scope
This documentation covers the complete Dataset Download module implementation in the main branch. It includes source acquisition, archive handling, extraction logic, Jenkins pipeline integration, and verification workflows.

**In Scope:**
- Google Drive source downloader
- Local source downloader (file and folder copy)
- Downloader Factory pattern implementation
- `download_dataset.py` orchestration
- `extract_dataset.py` extraction and merging
- `source_utils.py` utilities
- `downloader_factory.py` registry
- `google_drive.py` and `local.py` source implementations
- Jenkins Download Pipeline (`download_dataset_test.groovy`)
- `verify_download.py` and `verify_incoming.py`
- Download Flow, Incoming Folder Flow, Archive Extraction Flow
- Local Overwrite Policy
- Backward Compatibility

**Out of Scope:**
- S3, Azure Blob, FTP, or API sources
- Archive renaming or custom naming strategies
- Future features not yet implemented

## Quick Reference

| Component | File Path |
|-----------|-----------|
| Download Orchestrator | `scripts/python/common/download_dataset.py` |
| Extraction Orchestrator | `scripts/python/common/extract_dataset.py` |
| Source Utilities | `scripts/python/common/source_utils.py` |
| Downloader Factory | `scripts/python/common/factory/downloader_factory.py` |
| Google Drive Downloader | `scripts/python/common/downloaders/google_drive.py` |
| Local Downloader | `scripts/python/common/downloaders/local.py` |
| Download Verifier | `scripts/python/common/verify_download.py` |
| Incoming Verifier | `scripts/python/common/verify_incoming.py` |
| Jenkins Pipeline | `download_dataset_test.groovy` |
| Configuration | `config/common/dataset.conf` |

## Prerequisites
- Python 3.x with `gdown` library (for Google Drive)
- 7-Zip installed on Windows (for unsupported ZIP compression methods)
- Jenkins with Windows agent
- Git repository access

## Entry Points
- **Windows Batch:** `scripts/batch/common/download_dataset.bat`
- **PowerShell:** `scripts/powershell/common/download_dataset.ps1`
- **Jenkins:** `download_dataset_test.groovy`

## Configuration
Primary configuration file: `config/common/dataset.conf`

```properties
DATASET_URL=https://drive.google.com/file/d/...
DATASET_NAME=AutomationData_v3.zip
DOWNLOAD_DIRECTORY=incoming/archive
AUTO_EXTRACT=true
DELETE_ARCHIVE=false
FORCE_DOWNLOAD=false
SOURCE_TYPE=
SOURCE_PATH=
FORCE_EXTRACT=false
```

Environment variables override config file values.

## Related Documentation
- `01_OVERVIEW.md` - Module overview and concepts
- `02_ARCHITECTURE.md` - System architecture and diagrams
- `03_GOOGLE_DRIVE.md` - Google Drive source details
- `04_LOCAL_SOURCE.md` - Local source details
- `05_JENKINS_PIPELINE.md` - CI/CD pipeline documentation
- `06_TESTING_RESULTS.md` - Test execution results
- `07_BACKWARD_COMPATIBILITY.md` - Migration and compatibility notes
