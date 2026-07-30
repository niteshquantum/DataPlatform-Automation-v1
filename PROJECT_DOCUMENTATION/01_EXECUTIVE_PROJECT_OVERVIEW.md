# 01 — Executive Project Overview

## What this is

A **Database Automation Platform** that turns "install a database, deploy its schema, load a dataset, create
its objects, apply security roles, and prove it worked" into repeatable, parameterized automation that runs the
same way on Windows and Ubuntu Linux, both inside Jenkins and on a developer's laptop.

## One-sentence description

> A cross-operating-system, Jenkins-orchestrated automation framework that provisions and configures four
> databases, deploys schema via Liquibase, loads datasets, generates and deploys database objects, enforces
> role-based access control, and validates outcomes — all driven by shared Python/Batch/Bash scripts.

## The core idea: one automation, three doors

The project does **not** contain three separate implementations. It contains **one shared core** of automation
scripts and **three different front doors** to reach it:

1. **Main Jenkins pipeline** (`jenkins/Jenkinsfile`) — one job, parameterized by `DATABASE`, `ACTION`,
   `CLEANUP_MODE`, that fans out to the correct Jenkins agent (`windows-node` or `ubuntu-node`) and runs the
   right scripts.
2. **Standalone Jenkins pipelines** (`jenkins/<db>/<os>/setup|load|cleanup_pipeline.groovy`) — a focused Jenkins
   job for a single database + OS combination.
3. **Direct local execution** (`scripts/batch/.../*.bat` and `scripts/bash/.../*.sh`) — run the same scripts from
   a terminal with no Jenkins at all.

Because all three doors call the same batch/bash/Python scripts, the result is consistent regardless of how it is
launched.

## What it automates (capability map)

| Capability | Mechanism | Status |
|------------|-----------|--------|
| Install / start / stop database | Terraform `null_resource` + PowerShell/Bash | IMPLEMENTED |
| Deploy schema | Liquibase (`master.xml`) | IMPLEMENTED |
| Load dataset (CSV/JSON) | `data_loader.py` | IMPLEMENTED |
| Generate + deploy objects | Python generators → Liquibase `master_objects.xml` | IMPLEMENTED |
| Access control | RBAC CLI gate (`auth_cli.py`, `cli.py`) | IMPLEMENTED |
| Validation | Runtime/env/schema/data/object validators | IMPLEMENTED |
| Reporting | HTML + JSON reports, history | IMPLEMENTED |
| Migration analytics | Discovery / assessment / reconciliation / recommendation | IMPLEMENTED |

## Databases and operating systems

- **Databases:** MySQL, PostgreSQL, Microsoft SQL Server, MongoDB.
- **Operating systems:** Windows (Batch + PowerShell), Ubuntu (Bash).

## Why it matters

The platform removes manual, error-prone database setup from migration and onboarding projects, gives every run a
consistent report, and lets the same automation be driven centrally (Jenkins) or locally (developer laptop).

## Honesty about status

This overview is based on **static code inspection**. Several areas are partial or legacy (notably a legacy
`run_liquibase.py` runner that the pipelines do not use, and a missing `check_schema_changed.py` invoked by
`deploy_objects.bat`). These are detailed in `20_AS_BUILT_IMPLEMENTATION_STATUS.md`.

> See `23_DEMO_AND_EXPLANATION_GUIDE.md` for a manager-ready explanation and demo script.
