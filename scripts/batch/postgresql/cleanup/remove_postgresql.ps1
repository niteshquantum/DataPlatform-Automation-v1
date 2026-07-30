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

# =====================================================
# START REPORT
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL CLEANUP - REMOVE DEPLOYMENT"
Write-Log "======================================="
Write-Log ""

Write-Log "Project Root : $ProjectRoot"
Write-Log "PG Root      : $PgRoot"
Write-Log "Cleanup Mode : $CleanupMode"

# =====================================================
# CHECK POSTGRESQL ROOT
# =====================================================

if (!(Test-Path $PgRoot)) {

    Write-Log ""
    Write-Log "PostgreSQL deployment directory does not exist."
    Write-Log "Nothing to remove."

    Write-Log ""
    Write-Log "======================================="
    Write-Log "POSTGRESQL REMOVAL COMPLETED"
    Write-Log "======================================="

    exit 0
}

# =====================================================
# PRESERVE DATA MODE
# =====================================================

if ($CleanupMode -eq "PRESERVE_DATA") {

    Write-Log ""
    Write-Log "PRESERVE_DATA mode selected."
    Write-Log "PostgreSQL data directory will be preserved."

    $DeploymentDirectories = @(
        $PgBin,
        $PgLib,
        $PgShare
    )

    foreach ($Directory in $DeploymentDirectories) {

        if (Test-Path $Directory) {

            Write-Log "Removing directory: $Directory"

            Remove-Item `
                -Path $Directory `
                -Recurse `
                -Force

            if (Test-Path $Directory) {
                throw "Failed to remove directory: $Directory"
            }

            Write-Log "Removed successfully: $Directory"
        }
        else {
            Write-Log "Directory does not exist. Skipping: $Directory"
        }
    }

    if (Test-Path $PgData) {

        Write-Log ""
        Write-Log "Data directory preserved successfully."
        Write-Log "Preserved Data: $PgData"
    }
    else {

        Write-Log ""
        Write-Log "Data directory does not exist."
        Write-Log "Nothing available to preserve."
    }
}

# =====================================================
# DELETE DATA MODE
# =====================================================

elseif ($CleanupMode -eq "DELETE_DATA") {

    Write-Log ""
    Write-Log "DELETE_DATA mode selected."
    Write-Log "Entire project PostgreSQL deployment will be removed."

    Write-Log "Removing directory: $PgRoot"

    Remove-Item `
        -Path $PgRoot `
        -Recurse `
        -Force

    if (Test-Path $PgRoot) {
        throw "Failed to remove PostgreSQL deployment directory: $PgRoot"
    }

    Write-Log "Entire PostgreSQL deployment removed successfully."
}

# =====================================================
# FINAL VALIDATION
# =====================================================

Write-Log ""
Write-Log "Validating PostgreSQL deployment removal..."

if ($CleanupMode -eq "PRESERVE_DATA") {

    if (Test-Path $PgBin) {
        throw "PostgreSQL bin directory still exists."
    }

    if (Test-Path $PgLib) {
        throw "PostgreSQL lib directory still exists."
    }

    if (Test-Path $PgShare) {
        throw "PostgreSQL share directory still exists."
    }

    Write-Log "Deployment binaries removed successfully."

    if (Test-Path $PgData) {
        Write-Log "PostgreSQL data directory remains preserved."
    }
}

elseif ($CleanupMode -eq "DELETE_DATA") {

    if (Test-Path $PgRoot) {
        throw "PostgreSQL deployment directory still exists."
    }

    Write-Log "PostgreSQL deployment and data removed successfully."
}

# =====================================================
# SUCCESS
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL REMOVAL COMPLETED"
Write-Log "======================================="
Write-Log ""

Write-Log "Cleanup Mode : $CleanupMode"

if ($CleanupMode -eq "PRESERVE_DATA") {
    Write-Log "Data Status  : PRESERVED"
}
else {
    Write-Log "Data Status  : DELETED"
}

exit 0