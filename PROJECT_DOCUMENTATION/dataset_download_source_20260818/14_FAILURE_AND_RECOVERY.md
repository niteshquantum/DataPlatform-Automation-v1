# Failure and Recovery

## Failure Categories

### 1. Invalid Source Path

**Trigger:** `SOURCE_PATH` points to non-existent file/folder  
**Behavior:** `FileNotFoundError` raised by downloader  
**Recovery:** User corrects `SOURCE_PATH` and re-runs pipeline  
**Archive Impact:** None — no archive created or modified

### 2. Invalid/Non-ZIP Archive

**Trigger:** Source file is not a valid ZIP (e.g., HTML content)  
**Behavior:** `BadZipFile: File is not a zip file`  
**Recovery:** User provides valid ZIP or changes source  
**Archive Impact:** Existing valid archive preserved (if validation occurs after temp download)

### 3. Corrupted ZIP

**Trigger:** ZIP file is truncated or structurally damaged  
**Behavior:** `BadZipFile` or `ValueError: Corrupt archive entry`  
**Recovery:** User provides valid source archive  
**Archive Impact:** Existing valid archive preserved

### 4. Archive with No Data Files

**Trigger:** ZIP contains no `.csv` or `.json` files  
**Behavior:** `ValueError: Archive contains no supported data files (.csv or .json)`  
**Recovery:** User provides archive with valid data files  
**Archive Impact:** Existing valid archive preserved

### 5. Source Identity Mismatch

**Trigger:** Different source supplied with `FORCE_DOWNLOAD=false`  
**Behavior:** `SOURCE IDENTITY MISMATCH` warning, fresh download proceeds  
**Recovery:** Automatic — new source is downloaded and replaces active archive  
**Archive Impact:** Active archive replaced with new validated archive

### 6. Validation Failure During Download

**Trigger:** Downloaded file fails validation after successful copy  
**Behavior:** Temporary file removed, existing archive re-validated, exception propagated  
**Recovery:** Automatic retry or manual intervention  
**Archive Impact:** Existing valid archive preserved

### 7. Extraction Cleanup Failure

**Trigger:** Permission error or OS lock during stale folder removal  
**Behavior:** Warning logged, extraction continues or fails based on severity  
**Recovery:** Manual cleanup or re-run with `FORCE_EXTRACT=true`  
**Archive Impact:** Archive preserved

### 8. Extraction Failure

**Trigger:** Disk full, permission error, corrupt archive during extraction  
**Behavior:** `EXTRACTED_INVALID` state saved, exception propagated  
**Recovery:** Fix underlying issue, re-run pipeline  
**Archive Impact:** Archive preserved (extraction state marked invalid)

### 9. Recovery After Extraction Failure

**Trigger:** Re-running pipeline after `EXTRACTED_INVALID` state  
**Behavior:**
1. State shows `EXTRACTED_INVALID`
2. Pipeline detects incomplete extraction
3. Fresh extraction is forced
4. State returns to `EXTRACTED_COMPLETE` on success

**Archive Impact:** Archive remains unchanged

## Preservation Rules

| Failure Scenario | Existing Archive Preserved | Extraction State |
|------------------|---------------------------|------------------|
| Invalid source path | N/A (no archive) | N/A |
| Non-ZIP source | YES | Unchanged |
| Corrupted ZIP | YES | Unchanged |
| No data files | YES | Unchanged |
| Validation failure | YES | Unchanged |
| Extraction cleanup failure | YES | May become `EXTRACTED_INVALID` |
| Extraction failure | YES | `EXTRACTED_INVALID` |
| Source mismatch | Replaced with new validated archive | Reset |

## No False SUCCESS Guarantee

The following conditions guarantee no false SUCCESS:
1. Archive validation runs before any replacement
2. Validation must pass before `tmp_path.replace(output_file)`
3. On validation failure, exception is raised after cleanup
4. `Status: SUCCESS` is only printed after successful download AND validation
5. Extraction state is only marked `EXTRACTED_COMPLETE` after successful extraction AND verification
