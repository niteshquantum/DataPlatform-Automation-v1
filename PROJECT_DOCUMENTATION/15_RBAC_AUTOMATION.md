# 15 — RBAC Automation

## What RBAC is doing in this automation

RBAC is a **gate in front of every Jenkins entry point**. Before any database work runs, the pipeline
authenticates the caller and checks they have permission for the requested `<database>.<action>`. If not, the
run is denied. A `Viewer` role is allowed only to read the published executive report.

## Files (actual)

| File | Role |
|------|------|
| `rbac/auth.py` | `authenticate(user,pass)` against `credentials.json` (SHA256) |
| `rbac/authorization.py` | `has_permission(role, permission)` from `roles.json` |
| `rbac/utils.py` | JSON load + `hash_password`/`verify_password` (SHA256) |
| `rbac/cli.py` | CLI: authenticate + authorize; prints `AUTHORIZED:<role>` or `ACCESS_DENIED` |
| `rbac/auth_cli.py` | CLI: authenticate only; prints role (last line used by Jenkinsfile) |
| `rbac/credentials.json` | users (username, sha256 password, role, enabled) |
| `rbac/roles.json` | role → permission list |
| `rbac/permissions.json` | permission display names |

## Permission model

- Permissions are string keys `<database>.<action>`: e.g. `postgresql.setup`, `mysql.load`, `mssql.cleanup`,
  `report.view`.
- Roles: `Admin` (all setup/load/cleanup + report), `Developer` (no cleanup), `QA` (load + report),
  `Viewer` (report.view only).
- The Jenkinsfile computes `permission = "${database}.${action}".toLowerCase()` and passes it to `cli.py`.

## Flow (verified, Jenkins only)

```
Jenkinsfile executePipeline:
  auth_cli.py --username --password        -> prints role (last line)
    if role == Viewer -> publish executive report, return
  cli.py --username --password --permission "<db>.<action>"
    -> authenticate (credentials.json SHA256)
    -> has_permission(role, permission)   (roles.json)
    -> exit 0 AUTHORIZED / 1 AUTH_FAILED / 2 ACCESS_DENIED
  (non-zero exit fails the Jenkins stage)
```

## Integration with other subsystems

- **Jenkins:** RBAC wraps `executePipeline` in the main Jenkinsfile (Mode 1). Standalone `.groovy`
  pipelines verified do **not** invoke RBAC.
- **Liquibase / Database Objects:** RBAC gates the *action*; it does not create DB users/privileges.
- **Database:** RBAC is the platform's access control, separate from the database's own user model.

## Status

- CLI authentication + authorization gate: **IMPLEMENTED** (verified by code).
- Applied in Main Jenkins: **IMPLEMENTED**. In standalone/local modes: **NOT CONNECTED** (no RBAC call).
- Credentials stored as SHA256 hashes (good); but `USERNAME`/`PASSWORD` are passed on the command line
  (visible in Jenkins console / process args). See Security notes in status doc.
