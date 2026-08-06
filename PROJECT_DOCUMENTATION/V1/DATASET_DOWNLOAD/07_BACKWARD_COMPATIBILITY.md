# Backward Compatibility

## Title
Dataset Download Module - Backward Compatibility

## Purpose
Documents backward compatibility considerations, migration paths, and breaking changes (if any) for the Dataset Download module.

## Scope
Covers configuration compatibility, state file compatibility, pipeline compatibility, and upgrade considerations.

## Configuration Compatibility

### Config File Format
- **Current format:** `config/common/dataset.conf` (KEY=VALUE text format)
- **Breaking changes:** None in current implementation
- **Migration:** No migration required if using the standard `dataset.conf` format

### Environment Variable Precedence
Environment variables override config file values. This behavior is consistent and backward compatible:
```python
source_type = os.getenv("SOURCE_TYPE") or config.get("SOURCE_TYPE")
```

### Supported Configuration Keys
| Key | Required | Default | Description |
|-----|----------|---------|-------------|
| `DATASET_URL` | Conditional | - | Google Drive URL (required for google_drive source) |
| `DATASET_NAME` | Yes | - | Archive filename |
| `DOWNLOAD_DIRECTORY` | No | `incoming/archive` | Download destination |
| `AUTO_EXTRACT` | No | `true` | Extract after download |
| `DELETE_ARCHIVE` | No | `false` | Delete archive after extraction |
| `FORCE_DOWNLOAD` | No | `false` | Force re-download |
| `SOURCE_TYPE` | No | Auto-detect | Source type (`google_drive` or `local`) |
| `SOURCE_PATH` | Conditional | - | Source path (required for local source) |
| `FORCE_EXTRACT` | No | `false` | Force re-extraction |

**Backward Compatibility Note:** Existing `dataset.conf` files without `SOURCE_TYPE` or `SOURCE_PATH` keys continue to work. The module auto-detects `google_drive` if `DATASET_URL` is present.

## State File Compatibility

### State File Location
`metadata/common/dataset_state.json`

### State Schema Version
Current version: `"1.0"`

### Migration from Earlier Versions
- If `state_version` is missing, the module treats the state as empty (returns `{}`)
- Missing fields are handled gracefully via `.get()` with default values
- No automatic migration script is provided - state is rebuilt on next successful download

### State File Reset
```python
from scripts.python.common.dataset_state import reset_state
reset_state()  # Deletes dataset_state.json
```

## Pipeline Compatibility

### Jenkins Pipeline
- **Current:** `download_dataset_test.groovy`
- **Breaking changes:** None
- **Parameter names:** `DATABASE`, `SOURCE_TYPE`, `SOURCE_PATH`
- **Compatibility:** Existing Jenkins jobs using these parameters continue to work

### Entry Points
| Entry Point | Status | Notes |
|-------------|--------|-------|
| `download_dataset.bat` | Supported | Windows batch entry point |
| `download_dataset.ps1` | Supported | PowerShell orchestrator |
| `download_dataset.py` | Supported | Direct Python execution |

## Downloader Compatibility

### Adding New Downloaders
New downloaders can be added without modifying existing code:
1. Create a new module in `scripts/python/common/downloaders/`
2. Define `SOURCE_TYPE` constant
3. Define `download(config, output_path)` function
4. Factory auto-registers the new downloader on import

**Backward Compatibility:** Existing downloaders (`google_drive`, `local`) are unaffected.

## Archive Handling Compatibility

### ZIP Compression
- Python `zipfile` module handles standard ZIP compression
- 7-Zip fallback handles unsupported compression (e.g., Deflate64)
- If 7-Zip is not available and archive uses unsupported compression, validation/extraction fails with `NotImplementedError`

### Non-Archive Files
- CSV and JSON files placed directly in `incoming/{database}/`
- No extraction required
- Backward compatible with existing non-archive workflows

## Directory Structure Compatibility

### Current Structure
```
project_root/
+-- config/common/dataset.conf
+-- scripts/python/common/
+-- incoming/
|   +-- archive/
|   +-- {database}/
+-- metadata/common/dataset_state.json
```

### Legacy Considerations
- The module computes `ROOT` as `Path(__file__).resolve().parents[3]` from `scripts/python/common/`
- Moving the script files requires updating this path calculation
- No hardcoded paths are used beyond the `ROOT` calculation

## Breaking Changes (None in Current Version)
The current implementation has no breaking changes from the previously merged feature. All existing functionality is preserved.

## Upgrade Path

### From Pre-Feature Version
If upgrading from a version before the Dataset Download feature:
1. Ensure `config/common/dataset.conf` exists with required keys
2. Ensure Python dependencies include `gdown`
3. Ensure 7-Zip is installed on Windows agents
4. Run `python scripts/python/common/download_dataset.py` to test
5. Update Jenkins jobs to use new parameters if needed

### From Single-Source Version
If upgrading from a version with only Google Drive support:
1. No config changes required
2. `local` source is automatically available via factory
3. Set `SOURCE_TYPE=local` and `SOURCE_PATH=<path>` to use local source

## Deprecation Policy
No features are currently deprecated. Future deprecations will be announced in release notes with a minimum 2-version migration window.

## Testing After Upgrade
1. Run `verify_download.py` to confirm download path works
2. Run `verify_incoming.py` to confirm incoming folder structure
3. Execute `download_dataset_test.groovy` in Jenkins
4. Check `metadata/common/dataset_state.json` for proper state tracking
