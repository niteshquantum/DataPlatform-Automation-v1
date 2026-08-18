# Download Flow

## Layer-by-Layer Flow

```
Jenkins parameters / Environment variables
    ↓
withEnv([SOURCE_TYPE, SOURCE_PATH, FORCE_DOWNLOAD])
    ↓
Batch/Shell wrapper
    ↓
PowerShell (Windows) / Bash (Ubuntu)
    ↓
Python: download_dataset.py
    ↓
source_utils.get_output_filename()
    ↓
downloader_factory.get_downloader()
    ↓
Specific downloader (google_drive.py or local.py)
    ↓
Archive validation / state update
```

## Windows Entry Point

```
download_dataset.bat
    ↓
download_dataset.ps1
    ↓
python download_dataset.py
```

Environment variables are passed from Jenkins through `withEnv` into the batch context.

## Ubuntu Entry Point

```
download_dataset.sh
    ↓
python3 download_dataset.py
```

## Source Resolution in download_dataset.py

### SOURCE_TYPE Resolution
1. `os.getenv("SOURCE_TYPE")`
2. `config.get("SOURCE_TYPE")`
3. If `DATASET_URL` exists in config, defaults to `google_drive`
4. Otherwise raises `ValueError("SOURCE_TYPE is not configured.")`

### SOURCE_PATH Resolution
1. `os.getenv("SOURCE_PATH")`
2. `config.get("SOURCE_PATH")`

### Output Filename Resolution (`source_utils.py`)

| Source Type | Condition | Output Filename |
|-------------|-----------|-----------------|
| `local` | Source is `.zip` | `config["DATASET_NAME"]` |
| `local` | Source is folder/file | `Path(source_path).name` |
| `google_drive` | Always | `config["DATASET_NAME"]` |
| `None` | Always | `config["DATASET_NAME"]` |

### Destination Directory Resolution

| Archive? | Destination |
|----------|-------------|
| Yes | `project_root / config["DOWNLOAD_DIRECTORY"]` (e.g., `incoming/archive`) |
| No | `project_root / "incoming" / database.lower()` |

## FORCE_DOWNLOAD Behavior

```python
force = (
    os.getenv("FORCE_DOWNLOAD")
    or config.get("FORCE_DOWNLOAD", "false")
).lower() == "true"
```

When `FORCE_DOWNLOAD=true`:
- Existing archive reuse check is skipped
- Source is downloaded/copied fresh
- Existing valid archive is replaced after validation
