# Source Types

## Comparison Table

| Attribute | Google Drive | Local ZIP | Local Folder |
|-----------|-------------|-----------|--------------|
| Input | Drive share URL | `.zip` path | folder path |
| Destination | `incoming/archive/<DATASET_NAME>` | `incoming/archive/<DATASET_NAME>` | `incoming/<database>` |
| Database Resolution | Archive folder structure | Archive folder structure | Folder name |
| Is Archive | Yes | Yes | No |
| Requires FORCE_DOWNLOAD to re-download | Yes (SHA256 + URL identity) | Yes (SHA256 + path identity) | N/A (always copies) |
| Extraction | Optional (AUTO_EXTRACT) | Optional (AUTO_EXTRACT) | None |

## Google Drive

**Input:** Google Drive share URL  
**Example:** `https://drive.google.com/file/d/1J96umqV5NM9M4bDG238EYkJ5GsNJAYnC/view?usp=drive_link`

**Behavior:**
- Downloads via `gdown` library
- Saved as `incoming/archive/TestingDataset.zip` (from `config/common/dataset.conf` `DATASET_NAME`)
- Validated for ZIP integrity and `.csv`/`.json` content
- Extracted to `incoming/` if `AUTO_EXTRACT=true`
- State tracks source URL and archive SHA256

**Archive structure examples:**
```
mongodb/
mssql/
mysql/
postgresql/
```

or single database:
```
mysql/
```

## Local ZIP

**Input:** Path to a `.zip` file  
**Example:** `F:\Quantumatrix\Raw Data\testdatasmall.zip`

**Behavior:**
- Copied to `incoming/archive/TestingDataset.zip`
- Uses configured `DATASET_NAME` as active archive filename (not source filename)
- Validated for ZIP integrity and `.csv`/`.json` content
- Extracted to `incoming/` if `AUTO_EXTRACT=true`
- State tracks source path and archive SHA256

**Important:** All local ZIP sources share the same active archive filename (`DATASET_NAME`). This enables source identity comparison and atomic replacement when switching sources.

## Local Folder

**Input:** Path to a directory  
**Example:** `F:\Quantumatrix\Raw Data\mysql`

**Behavior:**
- Folder name resolves database: `mysql` → `incoming/mysql/`
- Only `.csv` and `.json` files are copied
- No archive is created
- No extraction stage runs
- No source identity tracking (always fresh copy)

**Examples:**
```
F:\Quantumatrix\Raw Data\mysql    → incoming\mysql\employees.csv
F:\Quantumatrix\Raw Data\mssql    → incoming\mssql\employees.csv
```

## Database Resolution Logic

1. `DATABASE` environment variable (highest priority)
2. Config file `DATABASE` value
3. Local folder name (when `SOURCE_TYPE=local` and source is a directory)
