# Source Identity and Reuse

## Source Identity Mechanism

The source identity system prevents unnecessary re-downloads when the same source is requested multiple times with `FORCE_DOWNLOAD=false`.

### Identity Check Sequence

```
Existing archive found
    ↓
Validate archive (ZIP integrity + data files)
    ↓
Load state from metadata/common/dataset_state.json
    ↓
Compare:
    - source_type
    - source_url (resolved from SOURCE_PATH or DATASET_URL)
    - archive_sha256
    ↓
Match? → REUSE / Skip download
Mismatch? → Download fresh
```

### State Fields Used for Identity

| Field | Purpose |
|-------|---------|
| `source_type` | `google_drive` or `local` |
| `source_url` | Resolved source path or URL |
| `archive_sha256` | SHA256 of the active archive file |
| `dataset_identity` | SHA256 of archive (alias for archive_sha256) |

## Same Source Reuse

**Input:** Same `SOURCE_TYPE` + same `SOURCE_PATH` + existing valid archive with matching SHA256

**Flow:**
1. `output_file.exists()` → True
2. `validate_archive(output_file)` → PASS
3. `load_state()` returns previous source_type, source_url, archive_sha256
4. Current values match previous values
5. **Result:** `ARCHIVE REUSE`, download skipped

**Logging:**
```
[INFO] Checking existing archive...
[INFO] ARCHIVE VALID
[INFO] Checking source identity...
[INFO] SOURCE IDENTITY MATCH
[INFO] ARCHIVE REUSE
[INFO] Download skipped.
```

## Different Source Replacement

**Input:** Different `SOURCE_PATH` + existing valid archive

**Flow:**
1. `output_file.exists()` → True
2. `validate_archive(output_file)` → PASS
3. `load_state()` returns previous source_type, source_url, archive_sha256
4. Current values differ from previous values
5. **Result:** `SOURCE IDENTITY MISMATCH`, download new source

**Logging:**
```
[WARNING] SOURCE IDENTITY MISMATCH
[WARNING] Current source: local / C:\...\source_b.zip
[WARNING] Previous source: local / C:\...\source_a.zip
[INFO] Downloading current source.
```

**Replacement sequence:**
1. Download new source to temporary file
2. Validate new archive completely
3. Atomically replace active archive
4. Update state with new source identity

## FORCE_DOWNLOAD=true

**Input:** Any source + `FORCE_DOWNLOAD=true`

**Flow:**
1. `output_file.exists() and not force` → False (force is True)
2. Skip reuse/identity check entirely
3. Download fresh to temporary file
4. Validate
5. Replace active archive
6. Update state

## Local ZIP Filename Fix

### Initial/Old Behavior
Local ZIP sources used the source filename as the output filename:
```
source_a.zip → incoming/archive/source_a.zip
source_b.zip → incoming/archive/source_b.zip
```

This meant:
- Switching from source_a to source_b created a NEW archive file
- The existing archive (source_a.zip) was never inspected
- Source identity comparison was bypassed
- Both archives accumulated in `incoming/archive/`

### Final Behavior
All local ZIP sources use the configured `DATASET_NAME` as the active archive filename:
```
source_a.zip → incoming/archive/TestingDataset.zip
source_b.zip → incoming/archive/TestingDataset.zip (replaces A)
```

This enables:
- Existing archive is always found at the same path
- Source identity comparison always runs
- Different sources trigger mismatch → replacement
- Only one active archive exists at a time

### Code Change
`scripts/python/common/source_utils.py` — `get_output_filename()`:
```python
if source_type == "local":
    if is_archive_file(source_path):
        return config["DATASET_NAME"]  # Fixed active archive name
    return Path(source_path).name       # Folders/files keep original name
```
