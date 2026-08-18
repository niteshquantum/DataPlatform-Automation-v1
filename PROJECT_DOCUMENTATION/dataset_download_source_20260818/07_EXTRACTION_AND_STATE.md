# Extraction and State

## Extraction Flow

```
Active archive (incoming/archive/TestingDataset.zip)
    ↓
extract_dataset.py
    ↓
validate_archive(archive_file)
    ↓
list_archive_folders(archive_file) → expected_folders
    ↓
load_state() → check extraction state
    ↓
[If fresh download or incomplete extraction]
    ↓
Clean previous extracted folders (from validated_extracted_structure)
    ↓
extract_and_merge_zip(archive_file, incoming_path)
    ↓
Actual extraction using zipfile (or 7-Zip fallback)
    ↓
Verify expected folders exist in incoming/
    ↓
build_extraction_state()
    ↓
save_state()
    ↓
EXTRACTED_COMPLETE
```

## Extraction Safety Rules

1. **Archive directory is NOT a database folder** — `incoming/archive/` is excluded from `validated_extracted_structure`
2. **Stale folders are cleaned** — Previous extracted folders from `validated_extracted_structure` that exist in `archive_top_structure` are removed before re-extraction
3. **Permission errors are handled** — Files are overwritten if direct unlink fails
4. **Extraction failure marks state invalid** — `EXTRACTED_INVALID` is set with error reason

## State File

Location: `metadata/common/dataset_state.json`

### Download State Fields

| Field | Description |
|-------|-------------|
| `state_version` | Schema version (`"1.0"`) |
| `dataset_identity` | SHA256 of archive |
| `source_type` | `google_drive` or `local` |
| `source_url` | Resolved source path or URL |
| `archive_filename` | From `config["DATASET_NAME"]` |
| `archive_path` | Full path to active archive |
| `archive_size_bytes` | Archive file size |
| `archive_sha256` | SHA256 of archive |
| `download_timestamp` | ISO8601 UTC timestamp |
| `download_status` | `DOWNLOADED_VALID` or `DOWNLOADED_INVALID` |
| `resolved_database` | Resolved database name (if applicable) |
| `detected_databases` | Sorted list of top-level folders in archive |

### Extraction State Fields

| Field | Description |
|-------|-------------|
| `extraction_timestamp` | ISO8601 UTC timestamp |
| `extraction_status` | `EXTRACTED_COMPLETE` or `EXTRACTED_INVALID` |
| `archive_top_structure` | Sorted top-level folders in archive |
| `validated_extracted_structure` | Sorted extracted folders (excluding archive dir) |
| `force_extract` | Config `FORCE_EXTRACT` value |
| `delete_archive` | Config `DELETE_ARCHIVE` value |

## Skip Logic

Extraction is skipped when ALL of:
1. `FORCE_EXTRACT` is false
2. No fresh download since last extraction (`download_timestamp <= extraction_timestamp`)
3. `extraction_status == "EXTRACTED_COMPLETE"`
4. State archive path matches current archive
5. State archive SHA256 matches current archive SHA256
6. All expected folders exist in `incoming/`

## Fresh Download Detection

```python
fresh_download = bool(
    download_ts
    and (not extraction_ts or download_ts > extraction_ts)
)
```

When `fresh_download` is True, extraction is forced even if previous extraction state is complete.
