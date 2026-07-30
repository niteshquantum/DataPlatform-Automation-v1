$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$cleanupMode = $env:CLEANUP_MODE

if ([string]::IsNullOrWhiteSpace($cleanupMode)) {
    $cleanupMode = "PRESERVE_DATA"
}

$cleanupMode = $cleanupMode.ToUpper()

$historyFile = "$ROOT\metadata\mongodb\data_load_history.jsonl"
$archiveDir  = "$ROOT\archive\mongodb"
$failedDir   = "$ROOT\failed\mongodb"
$incomingDir = "$ROOT\incoming\mongodb"

Write-Host ""
Write-Host "====================================="
Write-Host "MONGODB LOAD ARTIFACTS CLEANUP"
Write-Host "====================================="
Write-Host ""

Write-Host "Cleanup Mode  : $cleanupMode"
Write-Host "History File  : $historyFile"
Write-Host "Archive Path  : $archiveDir"
Write-Host "Failed Path   : $failedDir"
Write-Host "Incoming Path : $incomingDir"
Write-Host ""

if ($cleanupMode -notin @("PRESERVE_DATA", "DELETE_DATA")) {
    throw "Invalid CLEANUP_MODE: $cleanupMode. Allowed values: PRESERVE_DATA or DELETE_DATA"
}

# =====================================
# PRESERVE DATA MODE
# =====================================

if ($cleanupMode -eq "PRESERVE_DATA") {

    Write-Host "MongoDB data is being preserved."
    Write-Host "Load history, archive and failed artifacts will also be preserved."
    Write-Host "Incoming source files will remain untouched."

    Write-Host ""
    Write-Host "====================================="
    Write-Host "MONGODB LOAD ARTIFACTS PRESERVED"
    Write-Host "====================================="
    Write-Host ""

    exit 0
}

# =====================================
# DELETE LOAD HISTORY
# =====================================

Write-Host "Cleaning MongoDB data load history..."

if (Test-Path $historyFile) {

    Remove-Item -Path $historyFile -Force

    Write-Host "Data load history removed successfully."
}
else {
    Write-Host "Data load history not found. Nothing to remove."
}

# =====================================
# CLEAN ARCHIVE DIRECTORY CONTENTS
# =====================================

Write-Host ""
Write-Host "Cleaning MongoDB archive artifacts..."

if (Test-Path $archiveDir) {

    $archiveItems = Get-ChildItem -Path $archiveDir -Force

    if ($archiveItems) {

        $archiveItems | Remove-Item -Recurse -Force

        Write-Host "MongoDB archive artifacts removed successfully."
    }
    else {
        Write-Host "MongoDB archive directory is already empty."
    }
}
else {
    Write-Host "MongoDB archive directory not found. Nothing to remove."
}

# =====================================
# CLEAN FAILED DIRECTORY CONTENTS
# =====================================

Write-Host ""
Write-Host "Cleaning MongoDB failed artifacts..."

if (Test-Path $failedDir) {

    $failedItems = Get-ChildItem -Path $failedDir -Force

    if ($failedItems) {

        $failedItems | Remove-Item -Recurse -Force

        Write-Host "MongoDB failed artifacts removed successfully."
    }
    else {
        Write-Host "MongoDB failed directory is already empty."
    }
}
else {
    Write-Host "MongoDB failed directory not found. Nothing to remove."
}

# =====================================
# VALIDATION
# =====================================

Write-Host ""
Write-Host "Validating MongoDB load artifacts cleanup..."
Write-Host ""

if (Test-Path $historyFile) {
    throw "MongoDB data load history still exists after cleanup"
}

if (Test-Path $archiveDir) {

    $remainingArchiveItems = Get-ChildItem -Path $archiveDir -Force

    if ($remainingArchiveItems) {
        throw "MongoDB archive artifacts still exist after cleanup"
    }
}

if (Test-Path $failedDir) {

    $remainingFailedItems = Get-ChildItem -Path $failedDir -Force

    if ($remainingFailedItems) {
        throw "MongoDB failed artifacts still exist after cleanup"
    }
}

# IMPORTANT:
# incoming/mongodb is intentionally NOT deleted.

Write-Host "Data load history cleanup validated successfully."
Write-Host "Archive cleanup validated successfully."
Write-Host "Failed artifacts cleanup validated successfully."
Write-Host "Incoming source files preserved."

Write-Host ""
Write-Host "====================================="
Write-Host "MONGODB LOAD ARTIFACTS CLEANUP SUCCESSFUL"
Write-Host "====================================="
Write-Host ""

exit 0