# Jenkins Integration

## 1. Standalone Pipeline Integration

Each standalone pipeline defines its own parameters and stages:

### Parameters
```groovy
parameters {
    booleanParam(name: 'RUN_ASSESSMENT', ...)
    choice(name: 'SOURCE_TYPE', choices: ['google_drive', 'local'], ...)
    string(name: 'SOURCE_PATH', ...)
    booleanParam(name: 'FORCE_DOWNLOAD', ...)
}
```

### Download Dataset Stage
```groovy
stage('Download Dataset') {
    steps {
        script {
            runTrackedStage('Download Dataset') {
                withEnv([
                    "SOURCE_TYPE=${params.SOURCE_TYPE}",
                    "SOURCE_PATH=${params.SOURCE_PATH}",
                    "DATABASE=<database>",
                    "FORCE_DOWNLOAD=${params.FORCE_DOWNLOAD}"
                ]) {
                    bat 'scripts\\batch\\common\\download_dataset.bat'  // Windows
                    sh './scripts/bash/common/download_dataset.sh'      // Ubuntu
                }
            }
        }
    }
}
```

### Verify Download Stage
```groovy
stage('Verify Download') {
    steps {
        script {
            runTrackedStage('Verify Download') {
                bat 'python scripts\\python\\common\\verify_download.py'  // Windows
                sh 'python3 scripts/python/common/verify_download.py'    // Ubuntu
            }
        }
    }
}
```

**Files modified:**
- `CI_CD/mysql/windows/load_pipeline.groovy`
- `CI_CD/mysql/ubuntu/load_pipeline.groovy`
- `CI_CD/postgresql/windows/load_pipeline.groovy`
- `CI_CD/mssql/windows/load_pipeline.groovy`
- `CI_CD/mongodb/windows/load_pipeline.groovy`

## 2. Master Routed Pipeline Integration

### jenkins/Jenkinsfile

**Parameters added:**
```groovy
choice(name: 'SOURCE_TYPE', choices: ['google_drive', 'local'], ...)
string(name: 'SOURCE_PATH', defaultValue: '', ...)
booleanParam(name: 'FORCE_DOWNLOAD', defaultValue: false, ...)
```

**Context propagation:**
```groovy
def context = [
    database: env.ROUTED_DATABASE,
    action: env.ROUTED_ACTION,
    operatingSystem: env.ROUTED_OS,
    node: env.ROUTED_NODE,
    cleanupMode: params.CLEANUP_MODE,
    sourceType: params.SOURCE_TYPE,
    sourcePath: params.SOURCE_PATH,
    forceDownload: params.FORCE_DOWNLOAD
]
```

### jenkins/common/<database>/load_steps.groovy

**Download Dataset modification:**
```groovy
stage('Download Dataset') {
    steps {
        script {
            runTrackedStage('Download Dataset') {
                withEnv([
                    "SOURCE_TYPE=${context.sourceType}",
                    "SOURCE_PATH=${context.sourcePath}",
                    "FORCE_DOWNLOAD=${context.forceDownload}"
                ]) {
                    // OS-specific command preserved
                    bat 'scripts\\batch\\common\\download_dataset.bat'
                    sh './scripts/bash/common/download_dataset.sh'
                }
            }
        }
    }
}
```

**Verify Download added (where missing):**
```groovy
stage('Verify Download') {
    steps {
        script {
            runTrackedStage('Verify Download') {
                bat 'python scripts\\python\\common\\verify_download.py'
                sh 'python3 scripts/python/common/verify_download.py'
            }
        }
    }
}
```

## Files That Did NOT Need Changes

| File | Reason |
|------|--------|
| `jenkins/pipeline_config.groovy` | Routing only — node/OS/path resolution |
| `jenkins/common/common_stage_tracker.groovy` | Stage logging/tracking only |
| All `scripts/` files | Already support env var configuration |
| All batch/bash files | Already pass env vars to Python |

## Parameter Flow Summary

```
jenkins/Jenkinsfile
    ↓ params.SOURCE_TYPE / SOURCE_PATH / FORCE_DOWNLOAD
context map
    ↓ context.sourceType / sourcePath / forceDownload
jenkins/common/<database>/load_steps.groovy
    ↓ withEnv([...])
download_dataset.bat / download_dataset.sh
    ↓ os.getenv()
download_dataset.py
```
