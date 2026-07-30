param (
    [ValidateSet("PRESERVE_DATA", "DELETE_DATA")]
    [string]$CleanupMode = "PRESERVE_DATA"
)

$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)

    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$Timestamp] $Message"
}

function Get-ProjectRoot {

    $Root = Split-Path $PSScriptRoot -Parent
    $Root = Split-Path $Root -Parent
    $Root = Split-Path $Root -Parent
    $Root = Split-Path $Root -Parent

    return $Root
}

# =====================================================
# PROJECT PATHS
# =====================================================

$ProjectRoot = Get-ProjectRoot

$PgRoot  = Join-Path $ProjectRoot "databases\postgresql"
$PgBin   = Join-Path $PgRoot "bin"
$PgLib   = Join-Path $PgRoot "lib"
$PgShare = Join-Path $PgRoot "share"
$PgData  = Join-Path $PgRoot "data"

$TerraformDirectory = Join-Path $ProjectRoot "terraform\postgresql"

$TerraformState = Join-Path $TerraformDirectory "terraform.tfstate"

$TerraformStateBackup = Join-Path $TerraformDirectory "terraform.tfstate.backup"

$TerraformLockFile = Join-Path $TerraformDirectory ".terraform.tfstate.lock.info"

# =====================================================
# START REPORT
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL CLEANUP VALIDATION"
Write-Log "======================================="
Write-Log ""

Write-Log "Project Root : $ProjectRoot"
Write-Log "Cleanup Mode : $CleanupMode"

# =====================================================
# VALIDATE CLEANUP MODE
# =====================================================

if ($CleanupMode -eq "PRESERVE_DATA") {

    Write-Log ""
    Write-Log "Validating PRESERVE_DATA cleanup..."

    if (Test-Path $PgBin) {
        throw "Cleanup validation failed: PostgreSQL bin directory still exists."
    }

    Write-Log "PASS: PostgreSQL bin directory removed."

    if (Test-Path $PgLib) {
        throw "Cleanup validation failed: PostgreSQL lib directory still exists."
    }

    Write-Log "PASS: PostgreSQL lib directory removed."

    if (Test-Path $PgShare) {
        throw "Cleanup validation failed: PostgreSQL share directory still exists."
    }

    Write-Log "PASS: PostgreSQL share directory removed."

    if (Test-Path $PgData) {
        Write-Log "PASS: PostgreSQL data directory preserved."
    }
    else {
        Write-Log "INFO: PostgreSQL data directory does not exist."
    }
}

elseif ($CleanupMode -eq "DELETE_DATA") {

    Write-Log ""
    Write-Log "Validating DELETE_DATA cleanup..."

    if (Test-Path $PgRoot) {
        throw "Cleanup validation failed: PostgreSQL deployment directory still exists."
    }

    Write-Log "PASS: Entire PostgreSQL deployment removed."
}

# =====================================================
# VALIDATE TERRAFORM STATE
# =====================================================

Write-Log ""
Write-Log "Validating Terraform state cleanup..."

if (Test-Path $TerraformState) {
    throw "Cleanup validation failed: terraform.tfstate still exists."
}

Write-Log "PASS: terraform.tfstate removed."

if (Test-Path $TerraformStateBackup) {
    throw "Cleanup validation failed: terraform.tfstate.backup still exists."
}

Write-Log "PASS: terraform.tfstate.backup removed."

if (Test-Path $TerraformLockFile) {
    throw "Cleanup validation failed: Terraform state lock file still exists."
}

Write-Log "PASS: Terraform state lock file removed."

# =====================================================
# SUCCESS
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL CLEANUP VALIDATION PASSED"
Write-Log "======================================="
Write-Log ""

Write-Log "Cleanup Mode : $CleanupMode"
Write-Log "Status       : SUCCESS"

exit 0