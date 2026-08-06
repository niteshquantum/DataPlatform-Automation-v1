# Google Drive Source Implementation

## Title
Google Drive Downloader Implementation

## Purpose
Documents the Google Drive source implementation, its dependencies, configuration, error handling, and integration with the Downloader Factory pattern.

## Scope
Covers the `google_drive.py` module, its `download()` function signature, configuration requirements, and how it integrates with the rest of the Dataset Download module.

## Component Location
`scripts/python/common/downloaders/google_drive.py`

## Strategy Pattern Registration
- **SOURCE_TYPE:** `"google_drive"`
- **Registered by:** `downloader_factory.py` via automatic module discovery

## Dependencies
- **gdown** - Third-party Python library for Google Drive file downloads
- **os** - Environment variable access
- **pathlib.Path** - Path manipulation

## Configuration

### Required Configuration
| Parameter | Source | Description |
|-----------|--------|-------------|
| `SOURCE_PATH` | Env var or config | Google Drive direct download URL |
| `DATASET_NAME` | Config | Output filename for the downloaded file |
| `DATASET_URL` | Config | Fallback URL if SOURCE_PATH is not set |

### Configuration Precedence
1. Environment variable `SOURCE_PATH`
2. Config file `SOURCE_PATH`
3. Config file `DATASET_URL`

## Implementation Details

### Module Constant
```python
SOURCE_TYPE = "google_drive"
```

### Function Signature
```python
def download(config, output_path):
```

**Parameters:**
- `config` (dict): Loaded configuration from `dataset.conf`
- `output_path` (str): Destination file path for the downloaded dataset

**Behavior:**
1. Resolves source URL from `SOURCE_PATH` env var, then `SOURCE_PATH` config, then `DATASET_URL` config
2. Validates that a source URL is available
3. Calls `gdown.download(source_path, output_path, quiet=False)`
4. Validates the destination file exists post-download
5. Reports file size in megabytes

### Error Handling
| Error Condition | Behavior |
|-----------------|----------|
| No `SOURCE_PATH` or `DATASET_URL` configured | Raises `ValueError("SOURCE_PATH or DATASET_URL is not configured.")` |
| `gdown.download` fails to create file | Raises `RuntimeError("Google Drive download failed.")` |
| Network failures | Propagated from `gdown` library |

### Output Behavior
- Files are saved directly to the specified `output_path`
- The module does NOT create temporary files - temp file handling is managed by `download_dataset.py`
- Console output includes source URL, output file name, destination path, and file size

## Usage Example

### Via Environment Variable
```bash
set SOURCE_TYPE=google_drive
set SOURCE_PATH=https://drive.google.com/file/d/1ABC123/view?usp=sharing
python scripts/python/common/download_dataset.py
```

### Via Config File
```properties
# config/common/dataset.conf
SOURCE_TYPE=google_drive
SOURCE_PATH=https://drive.google.com/file/d/1ABC123/view?usp=sharing
DATASET_NAME=AutomationData_v3.zip
```

### Via Jenkins
```groovy
parameters {
    choice(name: 'SOURCE_TYPE', choices: ['google_drive', 'local'])
    string(name: 'SOURCE_PATH', defaultValue: 'https://drive.google.com/...')
}
```

## Integration Points

### With download_dataset.py
- Called via `downloader_factory.get_downloader("google_drive")`
- Invoked as `downloader.download(config, str(tmp_path))` for archives
- Invoked as `downloader.download(config, str(output_file))` for non-archives

### With verify_download.py
- `verify_download.py` checks if the downloaded file exists at the expected path
- Reports file size for archive files

### With extract_dataset.py
- Extracted files are placed in `incoming/` directory
- Archive path is passed to `extract_and_merge_zip()`

## Best Practices
- Ensure the Google Drive URL is a direct download link (not a preview page)
- Verify `gdown` is installed in the Python environment
- For large files, ensure sufficient disk space at the destination
- Network timeouts are handled by the `gdown` library - no custom timeout logic in this module

## Known Limitations
- Requires the `gdown` Python package
- Depends on Google Drive URL accessibility
- No built-in retry logic - retries are handled by `gdown` or the calling process
- Windows-specific entry points but Python code is cross-platform
