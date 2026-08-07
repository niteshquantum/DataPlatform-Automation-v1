# Local Source Implementation

## Title
Local Source Downloader Implementation

## Purpose
Documents the local filesystem source implementation, including file copy, folder copy with CSV/JSON filtering, overwrite policy, and integration with the Downloader Factory pattern.

## Scope
Covers the `local.py` module, its `download()` function signature, supported source types (file and directory), overwrite behavior, and configuration requirements.

## Component Location
`scripts/python/common/downloaders/local.py`

## Strategy Pattern Registration
- **SOURCE_TYPE:** `"local"`
- **Registered by:** `downloader_factory.py` via automatic module discovery

## Dependencies
- **os** - Environment variable access
- **shutil** - File and directory copy operations
- **pathlib.Path** - Path manipulation

## Supported Source Types

### 1. Local File
- Single file copy from source to destination
- Supports any file type (not limited to CSV/JSON)
- Overwrite policy applies

### 2. Local Directory
- Recursive copy of `.csv` and `.json` files only
- Creates destination directory if it does not exist
- Tracks new files vs overwritten files
- Raises `ValueError` if no CSV/JSON files found in source

### 3. Unsupported Source
- Raises `ValueError("Unsupported source: ...")` for any source type other than file or directory

## Configuration

### Required Configuration
| Parameter | Source | Description |
|-----------|--------|-------------|
| `SOURCE_PATH` | Env var or config | Path to local file or directory |

### Configuration Precedence
1. Environment variable `SOURCE_PATH`
2. Config file `SOURCE_PATH`

## Local Overwrite Policy

The local downloader implements an explicit overwrite policy:

| Scenario | Action | Behavior |
|----------|--------|----------|
| Destination does not exist | NEW | File is copied, verb printed: `copied` |
| Destination exists | OVERWRITE | File is replaced, verb printed: `replaced` |
| Copy operation fails | FAILED | Error printed with reason, exception re-raised |

### Overwrite Implementation Details
- Uses `shutil.copy2()` which preserves file metadata
- For files: overwrites directly with no backup
- For directories: iterates all entries, copies only `.csv` and `.json` files
- Counts and reports: `new_count`, `overwrite_count`, `csv_count`, `json_count`

## Implementation Details

### Module Constant
```python
SOURCE_TYPE = "local"
```

### Function Signature
```python
def download(config, output_path):
```

**Parameters:**
- `config` (dict): Loaded configuration from `dataset.conf`
- `output_path` (str): Destination file or directory path

**Behavior - File Source:**
1. Resolves `SOURCE_PATH` from env var or config
2. Validates source file exists
3. Creates destination parent directory if needed
4. Checks if destination exists (NEW vs OVERWRITE)
5. Copies file with `shutil.copy2()`
6. Prints summary with action and verb

**Behavior - Directory Source:**
1. Resolves `SOURCE_PATH` from env var or config
2. Validates source directory exists
3. Creates destination directory if needed
4. Iterates source directory entries
5. Filters for `.csv` and `.json` files only
6. Copies each file with `shutil.copy2()`
7. Tracks and prints new/overwritten counts
8. Raises `ValueError` if total files copied is zero

### Error Handling
| Error Condition | Behavior |
|-----------------|----------|
| No `SOURCE_PATH` configured | Raises `ValueError("SOURCE_PATH is not configured.")` |
| Source path does not exist | Raises `FileNotFoundError(f"Local dataset not found: {source}")` |
| Source is neither file nor directory | Raises `ValueError(f"Unsupported source: {source}")` |
| Directory contains no CSV/JSON files | Raises `ValueError(f"No CSV/JSON files found in: {source}")` |
| Copy operation fails | Prints error, re-raises exception |

## Output Behavior

### File Copy Output
```
Source File : data.csv
[OVERWRITE]
data.csv replaced.
```

### Directory Copy Output
```
Scanning local folder...
[NEW]
customers.csv copied.
[OVERWRITE]
orders.csv replaced.

Local Dataset Summary
---------------------
CSV Files              : 2
JSON Files             : 1
Total Files            : 3
Total Files Copied     : 1
Total Files Overwritten: 2
Target Folder          : C:\project\incoming\postgresql
```

## Usage Example

### Single File
```bash
set SOURCE_TYPE=local
set SOURCE_PATH=F:\Quantumatrix\Projects\rawd\customers.csv
python scripts/python/common/download_dataset.py
```

### Directory
```bash
set SOURCE_TYPE=local
set SOURCE_PATH=F:\Quantumatrix\Projects\rawd
set DATABASE=postgresql
python scripts/python/common/download_dataset.py
```

### Via Jenkins
```groovy
parameters {
    choice(name: 'SOURCE_TYPE', choices: ['google_drive', 'local'])
    string(name: 'SOURCE_PATH', defaultValue: 'F:\\Quantumatrix\\Projects\\rawd')
    choice(name: 'DATABASE', choices: ['postgresql', 'mysql', 'mongodb', 'mssql'])
}
```

## Integration Points

### With download_dataset.py
- Called via `downloader_factory.get_downloader("local")`
- For directories: `output_file` is set to `destination_directory` (not a file path)
- For files: `output_file` is set to `destination_directory / output_filename`
- Temp file logic in `download_dataset.py` is bypassed for local sources (no `.tmp` handling)

### With verify_download.py
- For directories: counts and lists all files in incoming directory
- For files: verifies the single file exists

### With extract_dataset.py
- Not directly involved in extraction
- Non-archive files skip extraction entirely

## Best Practices
- Ensure source paths use absolute paths or paths resolvable from the project root
- For directory sources, organize CSV and JSON files at the root level (no recursive scanning)
- Use `FORCE_DOWNLOAD=true` to re-copy files that may have changed
- Monitor the overwrite count in logs to detect unexpected source changes

## Known Limitations
- Directory copy scans only the top level of the source directory (no recursive subdirectory scanning)
- Only `.csv` and `.json` files are copied from directories
- No file deduplication or conflict resolution beyond simple overwrite
- Windows path separators should be used in Jenkins parameters
