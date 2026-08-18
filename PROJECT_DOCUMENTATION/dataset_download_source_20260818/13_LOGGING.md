# Logging

## Download Logging

### Fresh Download
```
============================================================
DATASET DOWNLOAD
============================================================

Source Type : LOCAL
Database    : mysql
Source Path : C:\...\source.zip
Destination : ...\incoming\archive

Copying local ZIP archive...

DOWNLOAD START

Source File : source.zip
[OVERWRITE]
source.zip replaced.
DOWNLOAD VALIDATION
ARCHIVE VALID
ARCHIVE REPLACEMENT

Source Type : LOCAL
Source Path : C:\...\source.zip
Archive     : ...\incoming\archive\TestingDataset.zip
Archive Size: 148 bytes
SHA256      : 629dfbb058dedc3e3f434dacca4e223d44150574a6559b4b7c700ce6220d9005
Detected Databases:
  mysql
[INFO] Archive downloaded successfully.
[INFO] Dataset state updated.

============================================================
DATASET SUMMARY
============================================================
Source Type : LOCAL
Source Path : C:\...\source.zip
Input Type  : ZIP Archive
Archive     : ...\incoming\archive\TestingDataset.zip
Archive Size: 148 bytes
SHA256      : 629dfbb058dedc3e3f434dacca4e223d44150574a6559b4b7c700ce6220d9005
Detected Databases:
  mysql
Status      : SUCCESS
```

### Archive Reuse
```
============================================================
DATASET DOWNLOAD
============================================================

[INFO] Checking existing archive...
[INFO] ARCHIVE VALID
[INFO] Checking source identity...
[INFO] SOURCE IDENTITY MATCH
[INFO] ARCHIVE REUSE
[INFO] Download skipped.

============================================================
DATASET SUMMARY
============================================================
Source Type : LOCAL
Destination : ...\incoming\archive
Input Type  : ZIP Archive
Detected Databases:
  mysql
Status      : SKIPPED
```

### Source Identity Mismatch
```
[WARNING] SOURCE IDENTITY MISMATCH
[WARNING] Current source: local / C:\...\source_b.zip
[WARNING] Previous source: local / C:\...\source_a.zip
[INFO] Downloading current source.
```

## Extraction Logging

### EXTRACTION START
```
============================================================
DATASET PREPARATION
============================================================

[INFO] Fresh archive download detected:
[INFO] Last Download   : 2026-08-18T10:30:00+00:00
[INFO] Forcing extraction of the freshly downloaded archive.

EXTRACTION START
[INFO] Removed previous extracted folder: mongodb
[INFO] Removed previous extracted folder: mssql
[INFO] Removed previous extracted folder: mysql
[INFO] Removed previous extracted folder: postgresql
[INFO] Extracting and merging dataset...
EXTRACTION SUCCESS
[SUCCESS] Dataset extracted and merged successfully.
```

### EXTRACTION SKIP
```
[INFO] Archive already extracted successfully.
[INFO] Skipping extraction.
```

### EXTRACTION FAILURE
```
EXTRACTION FAILURE
[ERROR] Extraction failed: ...
```

## Verification Logging

### Verify Download Success
```
============================================================
VERIFY DOWNLOAD
============================================================

[OK] Downloaded archive found:
  File : ...\incoming\archive\TestingDataset.zip
  Size : 0.14 MB

Download verification passed.
```

### Verify Download (Folder)
```
[OK] Downloaded files found:
  Directory : ...\incoming\mysql
  Files     : 3
    - employees.csv
    - orders.csv
    - products.csv

Download verification passed.
```

## Jenkins Stage Tracking

Each stage is wrapped with:
- `stage-start` — database, action, stage name
- `stage-end` — status SUCCESS or FAILURE
- `set-error` — on failure only

Platform-specific commands:
- Windows: `python scripts\logging\logger.py ...`
- Ubuntu: `python3 scripts/logging/logger.py ...`

## Duplicate Logging Fix

**Issue:** Fresh extraction printed duplicate markers:
```
EXTRACTION START
...
EXTRACTION START
EXTRACTION SUCCESS
[SUCCESS] Dataset extracted and merged successfully.
EXTRACTION SUCCESS
```

**Fix:** Removed duplicate `print("EXTRACTION START")` and `print("EXTRACTION SUCCESS")` from `extract_and_merge_zip()` in `scripts/python/common/extract_dataset.py`. The outer `extract_dataset()` still prints START once and SUCCESS once.
