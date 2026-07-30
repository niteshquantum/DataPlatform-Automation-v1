$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$dataDir = "$ROOT\databases\mysql\data"

Write-Host ""
Write-Host "====================================="
Write-Host "MYSQL DATA CLEANUP"
Write-Host "====================================="
Write-Host ""

# =====================================
# READ CLEANUP MODE
# =====================================

$cleanupMode = $env:CLEANUP_MODE

if ([string]::IsNullOrWhiteSpace($cleanupMode)) {
    $cleanupMode = "PRESERVE_DATA"
}

$cleanupMode = $cleanupMode.ToUpper()

Write-Host "Cleanup Mode : $cleanupMode"
Write-Host "Data Path    : $dataDir"
Write-Host ""

# =====================================
# VALIDATE CLEANUP MODE
# =====================================

if ($cleanupMode -notin @("PRESERVE_DATA", "DELETE_DATA")) {
    throw "Invalid CLEANUP_MODE: $cleanupMode. Allowed values: PRESERVE_DATA or DELETE_DATA"
}

# =====================================
# PRESERVE DATA
# =====================================

if ($cleanupMode -eq "PRESERVE_DATA") {

    Write-Host "Data deletion is disabled."
    Write-Host "MySQL data directory will be preserved."

    Write-Host ""
    Write-Host "====================================="
    Write-Host "MYSQL DATA PRESERVED SUCCESSFULLY"
    Write-Host "====================================="
    Write-Host ""

    exit 0
}

# =====================================
# CHECK DATA DIRECTORY
# =====================================

if (!(Test-Path $dataDir)) {

    Write-Host "MySQL data directory not found."
    Write-Host "Nothing to delete."

    Write-Host ""
    Write-Host "====================================="
    Write-Host "MYSQL DATA CLEANUP COMPLETED"
    Write-Host "====================================="
    Write-Host ""

    exit 0
}

# =====================================
# DELETE DATA
# =====================================

Write-Host "Deleting automation-managed MySQL data directory..."

Remove-Item $dataDir -Recurse -Force

# =====================================
# VALIDATE DATA REMOVAL
# =====================================

Write-Host ""
Write-Host "Validating MySQL data removal..."

if (Test-Path $dataDir) {
    throw "MySQL data directory still exists: $dataDir"
}

Write-Host ""
Write-Host "====================================="
Write-Host "MYSQL DATA REMOVED SUCCESSFULLY"
Write-Host "====================================="
Write-Host ""

exit 0