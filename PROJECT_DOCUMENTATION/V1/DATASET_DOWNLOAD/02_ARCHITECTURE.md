# Dataset Download Module - Architecture

## Title
Dataset Download Module Architecture

## Purpose
This document describes the internal architecture of the Dataset Download module, including component relationships, control flow, data flow, and the Strategy pattern implementation used for source abstraction.

## Scope
Covers the architectural design of all Python components, the downloader registry, state management, archive utilities, and the integration points with Jenkins CI/CD.

## System Architecture

### High-Level Component Diagram

```
+-------------------------------------------------------+
|                    CONFIGURATION                       |
|              config/common/dataset.conf                 |
+-------------------------------------------------------+
                            |
                            v
+-------------------------------------------------------+
|              ENTRY POINTS                              |
|  download_dataset.bat  ->  download_dataset.ps1        |
|       |                       |                        |
|       v                       v                        |
|  download_dataset.py      extract_dataset.py           |
+-------------------------------------------------------+
                            |
          +-----------------+-----------------+
          |                 |                 |
          v                 v                 v
+-----------------+ +-------------+ +-----------------+
| DOWNLOADER      | |  ARCHIVE    | |  STATE          |
| FACTORY         | |  UTILS      | |  MANAGEMENT     |
| (Strategy       | |             | |                 |
|  Pattern)       | |  validate   | |  dataset_state  |
|                 | |  extract    | |  .json          |
|  google_drive    | |  list       | |                 |
|  local           | |             | |                 |
+-----------------+ +-------------+ +-----------------+
          |                 |                 |
          v                 v                 v
+-------------------------------------------------------+
|              VERIFICATION LAYER                        |
|   verify_download.py        verify_incoming.py        |
+-------------------------------------------------------+
                            |
                            v
+-------------------------------------------------------+
|              JENKINS PIPELINE                          |
|           download_dataset_test.groovy                 |
+-------------------------------------------------------+
```

## Detailed Architecture

### Downloader Factory Pattern

The module implements the **Strategy Pattern** via `downloader_factory.py`. At import time, the factory discovers all modules in the `downloaders/` package and registers them in a `DOWNLOADERS` dictionary keyed by `SOURCE_TYPE`.

```
+---------------------+
|  downloader_factory |
+---------------------+
            |
            | iter_modules()
            v
+---------------------+     +---------------------+
|   google_drive.py   |     |      local.py       |
|  SOURCE_TYPE =      |     |  SOURCE_TYPE =      |
|  "google_drive"     |     |  "local"            |
+---------------------+     +---------------------+
            |                         |
            | download(config,        | download(config,
            |        output_path)     |        output_path)
            v                         v
      [gdown library]           [shutil.copy2]
```

**Key Characteristics:**
- Zero-configuration registration - any module with a `SOURCE_TYPE` constant and `download()` function is automatically registered
- Runtime source resolution based on config or environment variable
- Extensible - new sources can be added by dropping a new module into `downloaders/`

### Download Flow Architecture

```
+---------------------+
| download_dataset.py |
+---------------------+
            |
            | 1. Load config (dataset.conf)
            | 2. Resolve SOURCE_TYPE (env > config > auto-detect)
            | 3. Resolve SOURCE_PATH (env > config)
            | 4. Determine output filename
            | 5. Check if archive (.zip)
            |
            v
   +-------+-------+
   |               |
   v               v
+--------+    +------------+
| Archive|    | Non-Archive|
| Path   |    | Path       |
+--------+    +------------+
   |               |
   | destination = | destination = incoming/{database}/
   | incoming/     |
   | archive/      |
   v               v
+----------------------------------+
| Skip-if-exists logic             |
| - File exists?                   |
| - FORCE_DOWNLOAD?                |
| - Archive valid?                 |
+----------------------------------+
            |
            | Not skipping
            v
+----------------------------------+
| get_downloader(source_type)      |
+----------------------------------+
            |
            v
+----------------------------------+
| downloader.download(config,      |
|                   output_path)    |
+----------------------------------+
            |
            v
+----------------------------------+
| Post-download:                   |
| - Validate archive (if ZIP)      |
| - Build state JSON               |
| - Save state                     |
+----------------------------------+
```

### Archive Extraction Flow Architecture

```
+-----------------------+
| extract_dataset.py    |
+-----------------------+
            |
            | 1. Load config
            | 2. Resolve output filename
            | 3. Check if archive
            |
            v
   +-------+-------+
   |               |
   v               v
+--------+    +------------+
| Archive|    | Non-Archive|
| Path   |    | (skip)     |
+--------+    +------------+
   |
   | 4. Validate archive
   | 5. Create incoming/
   | 6. List archive folders
   | 7. Check state for skip
   |
   v
+----------------------------------+
| extract_and_merge_zip()          |
| - Python zipfile (default)       |
| - 7-Zip fallback (Deflate64)     |
| - Merge extraction               |
+----------------------------------+
            |
            v
+----------------------------------+
| Post-extraction:                 |
| - Verify expected folders exist  |
| - Check for CSV/JSON files       |
| - Build extraction state         |
| - Optionally delete archive      |
+----------------------------------+
```

### State Management Architecture

```
+----------------------------------+
|   metadata/common/               |
|   dataset_state.json             |
+----------------------------------+
            ^
            | save_state()
            |
+-----------------------+
|   dataset_state.py    |
+-----------------------+
| build_download_state()|
| build_extraction_state|
| mark_download_invalid()|
| mark_extraction_invalid|
| reset_state()         |
+-----------------------+
            |
            | Used by
            v
+-----------------------+
| download_dataset.py   |
| extract_dataset.py    |
+-----------------------+
```

**State Fields:**

| Field | Description |
|-------|-------------|
| `state_version` | State file schema version |
| `dataset_identity` | SHA256 of the archive file |
| `source_url` | Original DATASET_URL from config |
| `archive_filename` | DATASET_NAME from config |
| `archive_path` | Full path to downloaded archive |
| `archive_size_bytes` | Size of archive in bytes |
| `archive_sha256` | SHA256 checksum |
| `download_timestamp` | ISO timestamp of download |
| `download_status` | `DOWNLOADED_VALID` or `DOWNLOADED_INVALID` |
| `extraction_timestamp` | ISO timestamp of extraction |
| `extraction_status` | `EXTRACTED_COMPLETE` or `EXTRACTED_INVALID` |
| `archive_top_structure` | Top-level folders in archive |
| `validated_extracted_structure` | Folders found after extraction |
| `force_extract` | FORCE_EXTRACT config value |
| `delete_archive` | DELETE_ARCHIVE config value |

## Data Flow Diagrams

### Google Drive Source Data Flow

```
DATASET_URL (config) 
    |
    v
gdown.download(source_url, output_path)
    |
    v
tempfile.NamedTemporaryFile (.tmp)
    |
    v
validate_archive()
    |
    v
tmp_path.replace(output_file)
    |
    v
incoming/archive/{DATASET_NAME}
```

### Local Source Data Flow

```
SOURCE_PATH (env or config)
    |
    v
+---------------------+
| Source is file?     |----Yes----> shutil.copy2(source, output_file)
+---------------------+                |
| Source is dir?     |----Yes----> Iterate files (.csv, .json only)
+---------------------+                | shutil.copy2(file, target)
| Neither            |----Error---> raise ValueError
+---------------------+
```

### Archive Extraction Data Flow

```
incoming/archive/{name}.zip
    |
    v
zipfile.ZipFile (or 7-Zip fallback)
    |
    v
extractall(destination) / 7z x -o{destination}
    |
    v
incoming/{folder1}/
incoming/{folder2}/
...
    |
    v
Verify folders contain .csv/.json files
    |
    v
Build extraction state -> dataset_state.json
```

## Configuration Architecture

```
+----------------------------------+
|   ENVIRONMENT VARIABLES          |
|   (Highest Priority)             |
+----------------------------------+
            |
            | os.getenv("KEY") or
            v
+----------------------------------+
|   dataset.conf                   |
|   (KEY=VALUE format)             |
+----------------------------------+
            |
            | config.get("KEY")
            v
+----------------------------------+
|   HARDCODED DEFAULTS             |
|   (Lowest Priority)              |
+----------------------------------+
```

## Directory Structure

```
project_root/
+-- config/common/
|   +-- dataset.conf                    # Primary configuration
+-- scripts/python/common/
|   +-- download_dataset.py             # Download orchestrator
|   +-- extract_dataset.py              # Extraction orchestrator
|   +-- source_utils.py                 # Filename and archive detection
|   +-- verify_download.py              # Download verification
|   +-- verify_incoming.py              # Incoming folder verification
|   +-- config_loader.py                # Config loading utility
|   +-- dataset_state.py                # State tracking
|   +-- archive_utils.py                # 7-Zip and zipfile utilities
|   +-- factory/
|   |   +-- downloader_factory.py       # Strategy pattern registry
|   +-- downloaders/
|       +-- __init__.py                 # Package init
|       +-- google_drive.py             # Google Drive source
|       +-- local.py                    # Local filesystem source
+-- scripts/batch/common/
|   +-- download_dataset.bat            # Windows entry point
|   +-- set_project_root.bat            # Project root resolution
|   +-- install_7zip.bat                # 7-Zip installer
+-- scripts/powershell/common/
|   +-- download_dataset.ps1            # PowerShell orchestrator
+-- metadata/common/
|   +-- dataset_state.json              # Operational state
+-- incoming/
|   +-- archive/                        # Downloaded ZIP files
|   +-- {database}/                     # Extracted or direct files
+-- jenkins/
    +-- download_dataset_test.groovy     # CI/CD pipeline
```
