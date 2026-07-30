# 07 — Execution and Call Flow

This document maps **who calls whom**, grounded in `PROJECT_DOCUMENTATION/_evidence/execution_call_graph.csv`.

## 1. Top-level call flow (all modes)

```
ENTRY (Jenkinsfile | standalone .groovy | local .bat/.sh)
   |
   v
OS wrapper script (scripts/batch|bash/<db>/<phase>/*.bat|.sh)
   |
   +-- validate_* (python runtime, java runtime, tools, drivers)
   +-- Terraform deploy (install/start DB)        [setup only]
   +-- Liquibase run (schema / objects)           [setup + objects]
   +-- Python loaders (data_loader, generators)
   +-- Python engines (discovery/assessment/reconciliation)
   |
   v
DATABASE  +  metadata/  +  logs/  +  reports/
```

## 2. Main Jenkins call flow (example: PostgreSQL Setup, Windows)

```
jenkins/Jenkinsfile
  -> stage('PostgreSQL Setup') agent { label 'windows-node' }
     -> executePipeline('postgresql','setup','windows') {
          rbac/auth_cli.py        (authenticate)
          rbac/cli.py             (authorize permission "postgresql.setup")
          logger.py init
          sh/bat steps:
            validate_python_runtime
            install_python_requirements
            validate_python_requirements
            validate_java_runtime
            install_tools
            deploy_postgresql.bat  --> terraform/postgresql/main.tf (null_resource local-exec)
            configure_postgresql_service.bat
            create_database.bat
            run_liquibase.bat      --> tools/liquibase/liquibase (master.xml)
            configure_global_psql.bat
            validate_environment.bat
          logger.py finalize
          generate_report.py / generate_history.py
          archiveArtifacts(...)
        }
```

## 3. Standalone Jenkins call flow (example: postgresql/windows/setup_pipeline.groovy)

```
pipeline { agent any }
  stage('Initialize Logging')      -> logger.py init
  stage('Check Administrator...')  -> check_admin_privileges.bat (writes admin_status.txt)
  stage('Validate Python Runtime') -> validate_python_runtime.bat
  stage('Install Python Req')      -> install_python_requirements.bat
  stage('Validate Python Req')     -> validate_python_requirements.bat
  stage('Validate Java Runtime')   -> validate_java_runtime.bat
  stage('Install Tools')           -> install_tools.bat
  stage('Deploy PostgreSQL')       -> deploy_postgresql.bat (terraform)
  stage('Configure PG Service')    -> configure_postgresql_service.bat  [if admin]
  stage('Start PostgreSQL')        -> start_postgresql.bat              [if not admin]
  stage('Create Database')         -> create_database.bat
  stage('Run Liquibase')           -> run_liquibase.bat
  stage('Configure Global PSQL')   -> configure_global_psql.bat        [if admin]
  stage('Validate Environment')    -> validate_environment.bat
  post { always -> logger.py finalize; generate_report.py; generate_history.py; archiveArtifacts }
```

> Difference vs Main Jenkins: standalone uses `agent any` (needs to run on a Windows-capable node) and wraps each
> stage with `runTrackedStage()` (stage-start/stage-end/set-error logging). Main Jenkins centralizes RBAC + uses
> `when` guards on `currentBuild.number > 1`.

## 4. Direct Local call flow (example: postgresql_setup_pipeline.bat)

```
postgresql_setup_pipeline.bat
  -> set_project_root.bat
  -> validate_python_runtime.bat
  -> install_python_requirements.bat
  -> validate_python_requirements.bat
  -> validate_java_runtime.bat
  -> install_tools.bat
  -> deploy_postgresql.bat     (terraform)
  -> start_postgresql.bat
  -> create_database.bat
  -> run_liquibase.bat
  -> validate_environment.bat
  -> "POSTGRESQL SETUP SUCCESSFUL"
```

> Note: the direct-local `.bat`/`.sh` pipeline does **not** call `logger.py`/`generate_report.py` (no build
> numbers / Jenkins context). RBAC is also **not** applied in direct-local mode.

## 5. Data-loading call sub-flow (example: postgresql load)

```
load_data.bat / load_data.sh
  -> start_postgresql.bat        (ensure DB up)
  -> validate_postgresql.bat
  -> download_dataset.bat -> powershell download_dataset.ps1 -> python download_dataset.py
  -> schema_detector.py postgresql          (read schema metadata)
  -> generate_liquibase_xml.py              (dataset changelog)
  -> update_master_xml.py                   (rewrite master.xml with includes)
  -> run_liquibase.sh/.bat                  (apply schema)
  -> data_loader.py postgresql              (insert CSV/JSON; moves files archive/failed)
  -> validate_data.py / validate_loaded_data.bat
  -> deploy_objects.bat                     (objects via Liquibase master_objects.xml)
  -> assessment / reconciliation / discovery engines
```

## 6. Object deployment call sub-flow

```
deploy_objects.bat
  -> check_schema_changed.py   (MISSING — would error in direct-local mode)
  -> bootstrap_generator.py <db>
       -> ObjectDetector.detect()
       -> generate_views/functions/procedures/triggers/events/indexes/... (SQL)
       -> generate_liquibase_objects.py (XML changesets)
       -> generate_master_objects.py (master_objects.xml)
  -> deploy_objects.py <db>
       -> subprocess run_liquibase.bat|sh master_objects.xml
  -> validate_objects.bat
```

## 7. RBAC call sub-flow (Jenkins only)

```
Jenkinsfile stage
  -> rbac/auth_cli.py --username --password
       -> auth.authenticate -> utils.load_json(credentials.json) -> verify_password (SHA256)
       -> prints role (last line)
  -> if role == Viewer -> publish executive report, return
  -> rbac/cli.py --username --password --permission "<db>.<action>"
       -> auth.authenticate + authorization.has_permission(role, perm)
       -> exits 0 (AUTHORIZED) / 1 (AUTH_FAILED) / 2 (ACCESS_DENIED)
```

## 8. Evidence

Full caller→callee table: `PROJECT_DOCUMENTATION/_evidence/execution_call_graph.csv`.
File inventory: `PROJECT_DOCUMENTATION/_evidence/project_file_inventory.csv`.
