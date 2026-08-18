# Archive Validation

## Validation Layers

The archive validation system performs two checks:

1. **ZIP Structural Integrity** — `zipfile.testzip()` or 7-Zip `t` command
2. **Dataset Content Validation** — Presence of at least one `.csv` or `.json` file

## Validation Sequence

```
Download to temporary file
    ↓
zipfile.ZipFile(archive_path, "r")
    ↓
Has .csv/.json files? → NO → ValueError("Archive contains no supported data files")
    ↓
testzip() → Corrupt entry? → ValueError("Corrupt archive entry: ...")
    ↓
Validation PASS
```

## Python zipfile Path (Primary)

```python
with zipfile.ZipFile(archive_path, "r") as zf:
    if not _has_data_files(zf.namelist()):
        raise ValueError("Archive contains no supported data files (.csv or .json)")
    bad = zf.testzip()
    if bad is not None:
        raise ValueError(f"Corrupt archive entry: {bad}")
```

## 7-Zip Fallback Path

Used when Python `zipfile` raises `NotImplementedError` (e.g., Deflate64 compression):

```python
# Structural validation
result = subprocess.run([exe, "t", archive_path], ...)
if result.returncode != 0:
    raise ValueError("Archive validation failed.")

# Content listing
list_result = subprocess.run([exe, "l", archive_path], ...)
if not _has_data_files_7z(list_result.stdout):
    raise ValueError("Archive contains no supported data files (.csv or .json)")
```

## Temporary File Safety

```
with tempfile.NamedTemporaryFile(dir=destination_directory, delete=False, suffix=".tmp") as tmp:
    tmp_path = Path(tmp.name)

downloader.download(config, str(tmp_path))
validate_archive(tmp_path)   # ← Validation happens HERE
tmp_path.replace(output_file) # ← Atomic replacement only after validation
```

## Failure Behavior

When validation fails:
1. Temporary file is unlinked: `tmp_path.unlink(missing_ok=True)`
2. If existing archive exists, it is re-validated
3. If existing archive is invalid, it is removed: `output_file.unlink(missing_ok=True)`
4. Exception is propagated — no false SUCCESS
5. Existing valid archive remains untouched

## Tested Cases

| Case | Result |
|------|--------|
| Valid ZIP with `mysql/data.csv` | PASS — archive accepted |
| ZIP with no `.csv`/`.json` files | FAIL — `Archive contains no supported data files` |
| Non-ZIP file (HTML content) renamed `.zip` | FAIL — `BadZipFile: File is not a zip file` |
| Corrupted/truncated ZIP | FAIL — `BadZipFile: File is not a zip file` |
| Existing valid archive + invalid new source | PASS — existing archive preserved |
