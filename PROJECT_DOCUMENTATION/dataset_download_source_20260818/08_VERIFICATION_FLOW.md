# Verification Flow

## Verify Download

Runs immediately after Download Dataset stage.

### Windows
```groovy
runTrackedStage('Verify Download') {
    bat 'python scripts\\python\\common\\verify_download.py'
}
```

### Ubuntu
```groovy
runTrackedStage('Verify Download') {
    sh 'python3 scripts/python/common/verify_download.py'
}
```

### Behavior

**For archives:**
- Checks `incoming/archive/<output_filename>` exists
- Reports file size
- Does NOT validate archive contents (already validated during download)

**For non-archives (local folders):**
- Checks `incoming/<database>/` exists
- Reports file count and file names
- Does NOT validate file contents

**Environment:** No `DATABASE` environment variable is passed in the master routed pipeline. Database resolution is state-based when `DATABASE` is not explicitly provided.

## Verify Incoming

Runs after extraction (Ubuntu pipelines only, in current standalone implementations).

```groovy
runTrackedStage('Verify Incoming Folder') {
    withEnv(["DATABASE=mysql"]) {
        sh 'python3 scripts/python/common/verify_incoming.py'
    }
}
```

### Behavior
- Validates that expected database folders exist in `incoming/`
- Checks folder contents are non-empty
- Does NOT re-validate archive or extraction state

## Stage Responsibilities

| Stage | Responsibility | Validates |
|-------|----------------|-----------|
| Download Dataset | Acquire dataset source | Archive structure, data files, SHA256 |
| Verify Download | Confirm downloaded file exists | File presence, size |
| Verify Incoming | Confirm extracted folders exist | Folder structure, non-empty |

Do not merge these responsibilities. Each stage has a distinct validation scope.
