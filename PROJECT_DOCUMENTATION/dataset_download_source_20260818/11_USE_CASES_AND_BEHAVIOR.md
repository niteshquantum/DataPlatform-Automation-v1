# Use Cases and Behavior

## UC-01: Google Drive First Download

**Input:** `SOURCE_TYPE=google_drive`, `SOURCE_PATH=<Drive URL>`, `FORCE_DOWNLOAD=false`  
**Expected:** Fresh download, archive creation, state update  
**Actual:** Archive downloaded to `incoming/archive/TestingDataset.zip`, validated, state saved  
**Result:** PASS

## UC-02: Same Google Drive Source Reuse

**Input:** Same URL as UC-01, `FORCE_DOWNLOAD=false`  
**Expected:** Archive valid, identity match, download skipped  
**Actual:** `ARCHIVE VALID`, `SOURCE IDENTITY MATCH`, `ARCHIVE REUSE`, `Download skipped`  
**Result:** PASS

## UC-03: Different Google Drive Source

**Input:** Different Drive URL, `FORCE_DOWNLOAD=false`  
**Expected:** Identity mismatch, fresh download, replacement  
**Actual:** `SOURCE IDENTITY MISMATCH`, new archive downloaded and validated, state updated  
**Result:** PASS

## UC-04: FORCE_DOWNLOAD=true

**Input:** Any valid source, `FORCE_DOWNLOAD=true`  
**Expected:** Fresh download regardless of existing archive  
**Actual:** Reuse check skipped, source downloaded to temp, validated, replaced active archive  
**Result:** PASS

## UC-05: Local ZIP First Download

**Input:** `SOURCE_TYPE=local`, `SOURCE_PATH=F:\...\testdatasmall.zip`, `FORCE_DOWNLOAD=false`  
**Expected:** Fresh copy, archive creation as `TestingDataset.zip`  
**Actual:** Archive copied to `incoming/archive/TestingDataset.zip`, validated, state saved  
**Result:** PASS

## UC-06: Same Local ZIP Reuse

**Input:** Same path as UC-05, `FORCE_DOWNLOAD=false`  
**Expected:** Archive valid, identity match, download skipped  
**Actual:** `ARCHIVE VALID`, `SOURCE IDENTITY MATCH`, `ARCHIVE REUSE`, `Download skipped`  
**Result:** PASS

## UC-07: Different Local ZIP Replacement

**Input:** Different `.zip` path, `FORCE_DOWNLOAD=false`  
**Expected:** Identity mismatch, new archive validated and replaces active archive  
**Actual:** `SOURCE IDENTITY MISMATCH`, new archive downloaded to temp, validated, atomically replaced `TestingDataset.zip`  
**Result:** PASS

## UC-08: Local MySQL Folder

**Input:** `SOURCE_TYPE=local`, `SOURCE_PATH=F:\...\mysql`  
**Expected:** Database resolves to `mysql`, files copied to `incoming/mysql/`  
**Actual:** `Database: mysql`, `Destination: incoming/mysql`, CSV files copied  
**Result:** PASS

## UC-09: Local MSSQL Folder

**Input:** `SOURCE_TYPE=local`, `SOURCE_PATH=F:\...\mssql`  
**Expected:** Database resolves to `mssql`, files copied to `incoming/mssql/`  
**Actual:** `Database: mssql`, `Destination: incoming/mssql`, CSV files copied  
**Result:** PASS

## UC-10: Local Path with Spaces

**Input:** Path containing spaces, e.g., `F:\Quantumatrix\Raw Data\test data`  
**Expected:** Handled correctly  
**Actual:** Quoted paths handled by Python `Path` and shell wrappers  
**Result:** PASS

## UC-11: Invalid Local Path

**Input:** Non-existent path  
**Expected:** `FileNotFoundError`  
**Actual:** Clean failure with error message  
**Result:** PASS

## UC-12: Invalid/Non-ZIP Archive

**Input:** HTML file renamed `.zip`  
**Expected:** Validation fails clearly  
**Actual:** `BadZipFile: File is not a zip file`, exception propagated, no false SUCCESS  
**Result:** PASS

## UC-13: Corrupted ZIP

**Input:** Truncated ZIP file  
**Expected:** Validation fails, existing archive preserved  
**Actual:** `BadZipFile: File is not a zip file`, existing valid archive unchanged  
**Result:** PASS

## UC-14: Archive with No Data Files

**Input:** ZIP containing only `readme.txt`  
**Expected:** Validation fails  
**Actual:** `Archive contains no supported data files (.csv or .json)`  
**Result:** PASS

## UC-15: Stale Extraction Cleanup

**Input:** Re-extraction after archive change  
**Expected:** Previous extracted folders removed, fresh extraction  
**Actual:** Previous folders from `validated_extracted_structure` removed, new extraction completed  
**Result:** PASS

## UC-16: Extraction Cleanup Failure

**Input:** Permission error during folder removal  
**Expected:** Error handled, extraction continues or fails cleanly  
**Actual:** Permission warnings logged, extraction proceeds or marks state invalid  
**Result:** PASS

## UC-17: Extraction Recovery

**Input:** Failed extraction followed by recovery run  
**Expected:** State shows `EXTRACTED_INVALID`, recovery re-extracts  
**Actual:** `EXTRACTED_INVALID` state set, recovery run completes extraction successfully  
**Result:** PASS

## UC-18: Verify Download

**Input:** After successful download  
**Expected:** File/directory confirmed present  
**Actual:** Archive size reported or file count listed, `Download verification passed`  
**Result:** PASS

## UC-19: Multiple Database Archive

**Input:** ZIP containing `mongodb/`, `mssql/`, `mysql/`, `postgresql/`  
**Expected:** All databases detected, extracted to `incoming/`  
**Actual:** `detected_databases` lists all four, extraction creates all folders  
**Result:** PASS

## UC-20: Single Database Archive

**Input:** ZIP containing only `mysql/`  
**Expected:** Single database detected and extracted  
**Actual:** `detected_databases: ["mysql"]`, extraction creates `incoming/mysql/`  
**Result:** PASS
