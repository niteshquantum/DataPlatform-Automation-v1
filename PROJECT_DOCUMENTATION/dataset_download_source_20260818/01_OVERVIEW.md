# Dataset Download Source Handling — Overview

## Title
Dataset Download Source Handling

## Purpose
Enable runtime selection of dataset source type and location in Jenkins pipelines, replacing the previous requirement to manually edit configuration files before each pipeline run.

## Why This Feature Was Required
The original implementation required hardcoded or manually edited configuration in `config/common/dataset.conf` to switch between Google Drive and local sources. This was error-prone and prevented Jenkins users from selecting sources at build time.

## Supported Source Types

| Source Type | Input Format | Examples |
|-------------|--------------|----------|
| `google_drive` | Google Drive share URL | `https://drive.google.com/file/d/.../view?usp=drive_link` |
| `local` | Local filesystem path | `F:\Quantumatrix\Raw Data\mysql`, `/data/source.zip` |

Local sources support two input modes:
- **Local ZIP archive** — `.zip` file containing dataset folders
- **Local folder** — directory containing `.csv`/`.json` files organized by database

## Supported Platforms
- **Windows** — batch and PowerShell entry points
- **Ubuntu/Linux** — bash entry points

## Supported Databases
- MySQL
- PostgreSQL
- MSSQL
- MongoDB

## Jenkins Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `SOURCE_TYPE` | Choice | — | Select dataset source: `google_drive` or `local` |
| `SOURCE_PATH` | String | `''` | Dataset location (Google Drive URL or local path) |
| `FORCE_DOWNLOAD` | Boolean | `false` | Force dataset download instead of reusing an existing archive |

## Existing Pipeline Parameter
`RUN_ASSESSMENT` is an existing pipeline parameter unrelated to dataset download logic. It controls whether database assessment runs after a successful load.

## Final Goal
Users select `SOURCE_TYPE`, `SOURCE_PATH`, and `FORCE_DOWNLOAD` in Jenkins instead of modifying `dataset.conf`. The pipeline routes these values through the existing download, validation, extraction, and verification flow without changing database setup, loading, or assessment behavior.
