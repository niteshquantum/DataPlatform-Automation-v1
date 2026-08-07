# Dataset Download Module - Overview

## Title
Dataset Download Module Overview

## Purpose
The Dataset Download module automates the acquisition and preparation of raw datasets required for database migration pipelines. It provides a unified interface for downloading datasets from Google Drive or local filesystem, validates archive integrity, extracts contents, and verifies the incoming folder structure.

## Scope
This document provides a high-level overview of the module's capabilities, supported sources, core workflows, and operational boundaries.

## Key Concepts

### Source Types
The module supports two source types:
1. **google_drive** - Downloads files from Google Drive using the `gdown` library
2. **local** - Copies files or folders from the local filesystem

### Archive vs Non-Archive Routing
- **Archive (.zip) files** are downloaded to `incoming/archive/` and optionally extracted to `incoming/`
- **Non-archive files** (CSV, JSON) are placed directly in `incoming/{database}/`

### State Tracking
The module maintains a JSON state file at `metadata/common/dataset_state.json` that tracks:
- Download timestamps and status
- Extraction timestamps and status
- Archive SHA256 identity
- Folder structure validation

### Skip Logic
- **Download skip:** Existing valid archive + `FORCE_DOWNLOAD=false`
- **Extraction skip:** Complete extraction state + matching archive identity + expected folders present

## Supported Workflows

| Workflow | Description |
|----------|-------------|
| Download Flow | Acquire dataset from configured source |
| Incoming Folder Flow | Verify incoming directory has data |
| Archive Extraction Flow | Extract ZIP and merge into incoming folder |

## Configuration Model
- Primary config: `config/common/dataset.conf` (KEY=VALUE format)
- Environment variables override config values
- Config precedence: Env var > Config file > Default

## Dependencies
- `gdown` - Google Drive downloads
- `7-Zip` - Fallback for unsupported ZIP compression (Deflate64)
- Python standard library: `zipfile`, `shutil`, `pathlib`, `json`, `hashlib`

## Limitations
- Windows-focused execution (batch and PowerShell entry points)
- Only ZIP archive format supported for compression
- Local folder copy supports only `.csv` and `.json` files
- Google Drive requires `gdown` library
- 7-Zip required for archives with unsupported compression methods

## Best Practices
- Always validate configuration before pipeline execution
- Use `FORCE_DOWNLOAD=true` when source dataset has changed
- Use `FORCE_EXTRACT=true` when re-extraction is required
- Monitor `metadata/common/dataset_state.json` for operational status
- Run verification scripts after download and extraction stages
