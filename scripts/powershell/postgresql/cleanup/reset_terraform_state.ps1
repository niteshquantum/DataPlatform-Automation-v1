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

$TerraformDirectory = Join-Path $ProjectRoot "terraform\postgresql"

$TerraformState = Join-Path $TerraformDirectory "terraform.tfstate"

$TerraformStateBackup = Join-Path $TerraformDirectory "terraform.tfstate.backup"

$TerraformLockFile = Join-Path $TerraformDirectory ".terraform.tfstate.lock.info"

# =====================================================
# START REPORT
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL CLEANUP - TERRAFORM RESET"
Write-Log "======================================="
Write-Log ""

Write-Log "Project Root        : $ProjectRoot"
Write-Log "Terraform Directory : $TerraformDirectory"

# =====================================================
# CHECK TERRAFORM DIRECTORY
# =====================================================

if (!(Test-Path $TerraformDirectory)) {

    Write-Log "Terraform PostgreSQL directory does not exist."
    Write-Log "Nothing to reset."

    Write-Log ""
    Write-Log "======================================="
    Write-Log "TERRAFORM RESET COMPLETED"
    Write-Log "======================================="

    exit 0
}

# =====================================================
# REMOVE TERRAFORM STATE
# =====================================================

Write-Log ""
Write-Log "Checking Terraform state files..."

if (Test-Path $TerraformState) {

    Write-Log "Removing Terraform state:"
    Write-Log $TerraformState

    Remove-Item `
        -Path $TerraformState `
        -Force

    if (Test-Path $TerraformState) {
        throw "Failed to remove Terraform state file."
    }

    Write-Log "Terraform state removed successfully."
}
else {
    Write-Log "Terraform state does not exist. Skipping."
}

# =====================================================
# REMOVE TERRAFORM STATE BACKUP
# =====================================================

if (Test-Path $TerraformStateBackup) {

    Write-Log "Removing Terraform state backup:"
    Write-Log $TerraformStateBackup

    Remove-Item `
        -Path $TerraformStateBackup `
        -Force

    if (Test-Path $TerraformStateBackup) {
        throw "Failed to remove Terraform state backup."
    }

    Write-Log "Terraform state backup removed successfully."
}
else {
    Write-Log "Terraform state backup does not exist. Skipping."
}

# =====================================================
# REMOVE STALE LOCK FILE
# =====================================================

if (Test-Path $TerraformLockFile) {

    Write-Log "Removing stale Terraform lock file:"
    Write-Log $TerraformLockFile

    Remove-Item `
        -Path $TerraformLockFile `
        -Force

    if (Test-Path $TerraformLockFile) {
        throw "Failed to remove Terraform lock file."
    }

    Write-Log "Terraform lock file removed successfully."
}
else {
    Write-Log "Terraform lock file does not exist. Skipping."
}

# =====================================================
# FINAL VALIDATION
# =====================================================

Write-Log ""
Write-Log "Validating Terraform state reset..."

if (Test-Path $TerraformState) {
    throw "Terraform state still exists after reset."
}

if (Test-Path $TerraformStateBackup) {
    throw "Terraform state backup still exists after reset."
}

if (Test-Path $TerraformLockFile) {
    throw "Terraform lock file still exists after reset."
}

Write-Log "Terraform state reset validated successfully."

# =====================================================
# SUCCESS
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "TERRAFORM RESET COMPLETED"
Write-Log "======================================="
Write-Log ""

Write-Log "Terraform Directory : $TerraformDirectory"
Write-Log "State Status        : RESET"

exit 0