# 19 — End-to-End Workflows

All stages name actual files. Flows reuse the shared core (see `04`, `07`).

## A. SETUP (PostgreSQL Windows, direct-local equivalent)

```
postgresql_setup_pipeline.bat
  -> set_project_root.bat
  -> validate_python_runtime.bat
  -> install_python_requirements.bat -> validate_python_requirements.bat
  -> validate_java_runtime.bat
  -> install_tools.bat
  -> deploy_postgresql.bat
        -> terraform/postgresql/main.tf (null_resource local-exec)
        -> powershell/postgresql/install_windows.ps1
  -> start_postgresql.bat
  -> create_database.bat
  -> run_liquibase.bat        (applies liquibase/postgresql/master.xml)
  -> validate_environment.bat
```

## B. LOAD (PostgreSQL)

```
postgresql_load_pipeline.bat
  -> validate_python_runtime.bat
  -> validate_python_requirements.bat
  -> start_postgresql.bat -> validate_postgresql.bat
  -> download_dataset.bat -> powershell/download_dataset.ps1 -> python/download_dataset.py
  -> load_data.bat -> load_data.sh:
        schema_detector.py -> generate_liquibase_xml.py -> update_master_xml.py
        -> run_liquibase.sh -> data_loader.py -> validate_data.py
  -> validate_loaded_data.bat
  -> deploy_objects.bat (generate + deploy + validate)
  -> run_assessment.bat all -> generate_assessment_report.bat
  -> run_reconciliation.bat -> discovery/growth/requirement engines
  -> migration run_assessment/recommendation/action_plan/technical/executive reports
```

## C. OBJECTS (generic)

```
deploy_objects.bat
  -> bootstrap_generator.py <db>   (detect -> generate SQL -> generate XML -> master_objects.xml)
  -> deploy_objects.py <db>        (run_liquibase master_objects.xml)
  -> validate_objects.bat
```

## D. RBAC (Jenkins gate, before any action)

```
Jenkinsfile executePipeline:
  auth_cli.py --username --password        (role)
  cli.py --username --password --permission "<db>.<action>"   (allow/deny)
  (Viewer -> publish executive report, return)
```

## E. CLEANUP (where implemented)

```
<db>_cleanup_pipeline.bat / cleanup_pipeline.groovy
  -> withEnv CLEANUP_MODE=PRESERVE_DATA|DELETE_DATA
  -> scripts/<db>/cleanup/* (stop service, remove deployment,
     reset_terraform_state, drop database, validate_cleanup)
```
Cleanup pipelines exist for all four DBs on both OS (see `04` matrix).

## Notes

- MongoDB has no Liquibase/objects stage; its load/setup use mongo-native scripts.
- MSSQL Windows uses installer + `ConfigurationFile.template.ini`; Ubuntu uses container path.
- Main Jenkins wraps these same scripts with RBAC + logger + report.
