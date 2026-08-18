# Testing and Results

## Test Phases

### Phase 1: Google Drive Tests
- **Status:** PASS
- **Environment:** Windows standalone pipeline
- **Evidence:** `jenkintestoutputsdata/17aug/GOOGLE_DRIVE_TEST_*`

### Phase 2: Local Source Tests
- **Status:** PASS
- **Environment:** Windows standalone pipeline
- **Evidence:** `jenkintestoutputsdata/17aug/LOCAL_SOURCE_TEST_*`
- **Coverage:** Local ZIP, local folder, path with spaces, invalid path

### Phase 3: Archive Validation Tests
- **Status:** PASS
- **Environment:** Direct Python execution
- **Cases:** Valid ZIP, non-ZIP/HTML, corrupted ZIP, archive with no data files

### Phase 4: Extraction Failure/Recovery Tests
- **Status:** PASS
- **Environment:** Direct Python execution
- **Evidence:** `jenkintestoutputsdata/17aug/EXTRACTION_FAILURE_*`

### Phase 5: Windows Standalone Pipeline Integration
- **Status:** PASS
- **Files Modified:**
  - `CI_CD/mysql/windows/load_pipeline.groovy`
  - `CI_CD/postgresql/windows/load_pipeline.groovy`
  - `CI_CD/mssql/windows/load_pipeline.groovy`
  - `CI_CD/mongodb/windows/load_pipeline.groovy`

### Phase 6: Ubuntu Pipeline Integration
- **Status:** PASS
- **Files Modified:**
  - `CI_CD/mysql/ubuntu/load_pipeline.groovy`

### Phase 7: Source Identity and Reuse Tests
- **Status:** PASS
- **Tests:** Same-source reuse, different-source replacement, FORCE_DOWNLOAD=true

### Phase 8: Master Routing Integration
- **Status:** IMPLEMENTED
- **Files Modified:**
  - `jenkins/Jenkinsfile`
  - `jenkins/common/mysql/load_steps.groovy`
  - `jenkins/common/postgresql/load_steps.groovy`
  - `jenkins/common/mongodb/load_steps.groovy`
  - `jenkins/common/mssql/load_steps.groovy`

## Test Matrix

| ID | Scenario | Source | Expected | Result | Evidence |
|----|----------|--------|----------|--------|----------|
| T1 | Google Drive first download | Drive URL | Archive created | PASS | `#1.txt` |
| T2 | Local ZIP first download | `source.zip` | Archive created as `TestingDataset.zip` | PASS | `#2.txt` |
| T3 | Non-ZIP/HTML rejection | HTML as `.zip` | Validation fails | PASS | `#3.txt` |
| T4 | Corrupted ZIP rejection | Truncated ZIP | Validation fails, archive preserved | PASS | `#4.txt` |
| T5 | Same source reuse | Same ZIP | Download skipped | PASS | `#5.txt` |
| T6 | Different source replacement | Different ZIP | Identity mismatch, replacement | PASS | `#6.txt` |
| T7 | FORCE_DOWNLOAD=true | Any valid source | Fresh download | PASS | `#7.txt` |
| T8 | Invalid archive preservation | Invalid source | Existing archive unchanged | PASS | `#8.txt` |
| T9 | Local MySQL folder | Folder path | `incoming/mysql/` populated | PASS | `#9.txt` |
| T10 | Local MSSQL folder | Folder path | `incoming/mssql/` populated | PASS | `#10.txt` |
| T11 | Invalid local path | Missing path | `FileNotFoundError` | PASS | `#11.txt` |
| T12 | Extraction cleanup | Archive change | Previous folders removed | PASS | `#12.txt` |
| T13 | Extraction failure | Corrupt archive | `EXTRACTED_INVALID` | PASS | `#13.txt` |
| T14 | Extraction recovery | After failure | Re-extraction succeeds | PASS | `#14.txt` |
| T15 | Multiple database archive | Multi-folder ZIP | All databases extracted | PASS | `#15.txt` |
| T16 | Single database archive | Single-folder ZIP | One database extracted | PASS | `#16.txt` |
| T17 | Verify Download | After download | File confirmed | PASS | `#17.txt` |
| T18 | Windows standalone pipeline | Full pipeline | All stages pass | PASS | `#18.txt` |
| T19 | Ubuntu standalone pipeline | Full pipeline | All stages pass | PASS | `#19.txt` |

## Evidence Directories

- `jenkintestoutputsdata/17aug/` — Initial Windows test outputs
- `jenkintestoutputsdata/18aug/` — Follow-up test outputs
- `jenkintestoutputsdata/LOCAL_DATASET_SOURCE_TEST/` — Local source test artifacts
- `jenkintestoutputsdata/LOCAL_DATASET_TEST/` — Local dataset test artifacts

## Test Execution Notes

Tests T1-T10 were executed via direct Python invocation against `download_dataset.py`, `extract_dataset.py`, and `verify_download.py`.

Tests T11-T19 were executed via standalone Jenkins pipeline files (`CI_CD/*/windows/load_pipeline.groovy`, `CI_CD/mysql/ubuntu/load_pipeline.groovy`).

Master routing pipeline integration was validated via code inspection and diff review against the existing tested patterns.
