# 10 — Terraform Automation

## What Terraform actually does here

In this project Terraform is **not** used to provision cloud infrastructure. Every `terraform/<db>/main.tf` uses
only the **`null` provider** with **`provisioner "local-exec"`** to run **local scripts** that install and start
the database on the machine where Terraform runs.

### Verified example — `terraform/postgresql/main.tf`

- `required_providers { null = hashicorp/null ~> 3.2 }`, `required_version >= 1.13.0`.
- `locals.project_root = abspath("${path.module}/../..")` → repo root.
- `null_resource.install_postgresql_windows` → `local-exec` with `interpreter ["powershell.exe", ...]` running
  `scripts/powershell/postgresql/install_windows.ps1`.
- `null_resource.postgresql_install_linux` / `_start_linux` / `_validate_linux` → `local-exec` running
  `scripts/bash/postgresql/setup/install_postgresql.sh`, `start_postgresql.sh`, `validate_postgresql.sh`.
- `triggers = { always_run = timestamp() }` forces re-execution every apply (idempotency is handled by the scripts).

### How it is invoked

- `scripts/batch/postgresql/setup/deploy_postgresql.bat` runs:
  `terraform init` → `terraform validate` → `terraform apply -target=null_resource.install_postgresql_windows -auto-approve`.
- `scripts/bash/postgresql/setup/deploy_postgresql.sh` runs the same, targeting
  `null_resource.install_postgresql_linux` + `start_postgresql_linux`.
- The Terraform binary is expected at `tools/terraform/terraform[.exe]` (downloaded by `install_terraform` scripts).

## Exact boundaries

| Does | Does NOT |
|------|----------|
| Run `terraform init/validate/apply` locally | Create cloud VMs / networks |
| Call `local-exec` scripts that install/start DB | Manage remote state backends (uses local `.tfstate`) |
| Pass `project_root` to PowerShell/Bash | Deploy schema (Liquibase does that) |
| Re-run via `always_run` trigger | Load data or create RBAC |

## Other DBs

- `terraform/mysql/main.tf`, `terraform/mssql/main.tf`, `terraform/mongodb/main.tf` follow the same pattern
  (null_resource + local-exec → respective install scripts). `mongodb/main.tf` additionally has
  `terraform.tfvars` / `variables.tf`.
- `reset_terraform_state.bat/.ps1` scripts remove local `.tfstate` during cleanup.

## Why Terraform is used (simple language)

> Terraform gives us a single, declarative, re-runnable command (`terraform apply`) to install and start a database
> locally, instead of hand-running installers. Because it uses `local-exec`, it orchestrates the existing
> PowerShell/Bash install scripts — it is the "install/start" step of the pipeline, not a cloud provisioner.

## Status

- **IMPLEMENTED** (local-exec provisioning). Not verified at runtime (no `terraform apply` executed).
- `tools/terraform/` is an empty placeholder; the binary must be installed first or deploy scripts fail fast.
