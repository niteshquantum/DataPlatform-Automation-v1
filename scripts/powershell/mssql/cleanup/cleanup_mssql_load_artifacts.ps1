$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$CleanupMode = $env:CLEANUP_MODE

if ([string]::IsNullOrWhiteSpace($CleanupMode)) {
    $CleanupMode = "PRESERVE_DATA"
}

$CleanupMode = $CleanupMode.Trim().ToUpperInvariant()

$HistoryFile = "$ROOT\metadata\mssql\data_load_history.jsonl"
$ArchiveDir  = "$ROOT\archive\mssql"
$FailedDir   = "$ROOT\failed\mssql"
$IncomingDir = "$ROOT\incoming\mssql"

Write-Host ""
Write-Host "====================================="
Write-Host "MSSQL LOAD ARTIFACTS CLEANUP"
Write-Host "====================================="
Write-Host ""

Write-Host "Cleanup Mode  : $CleanupMode"
Write-Host "History File  : $HistoryFile"
Write-Host "Archive Path  : $ArchiveDir"
Write-Host "Failed Path   : $FailedDir"
Write-Host "Incoming Path : $IncomingDir"
Write-Host ""

# =====================================
# VALIDATE CLEANUP MODE
# =====================================

if ($CleanupMode -notin @("PRESERVE_DATA", "DELETE_DATA")) {
    throw "Invalid CLEANUP_MODE: $CleanupMode"
}

# =====================================
# PRESERVE DATA MODE
# =====================================

if ($CleanupMode -eq "PRESERVE_DATA") {

    Write-Host "MSSQL data is being preserved."
    Write-Host "Load history, archive and failed artifacts will also be preserved."
    Write-Host "Incoming source files will remain untouched."

    Write-Host ""
    Write-Host "====================================="
    Write-Host "MSSQL LOAD ARTIFACTS PRESERVED"
    Write-Host "====================================="
    Write-Host ""

    exit 0
}

# =====================================
# CLEAN DATA LOAD HISTORY
# =====================================

Write-Host "Cleaning MSSQL data load history..."

if (Test-Path -LiteralPath $HistoryFile) {

    Remove-Item `
        -LiteralPath $HistoryFile `
        -Force `
        -ErrorAction Stop

    Write-Host "Data load history removed successfully."
}
else {

    Write-Host "Data load history not found. Nothing to remove."
}

# =====================================
# CLEAN ARCHIVE ARTIFACTS
# =====================================

Write-Host ""
Write-Host "Cleaning MSSQL archive artifacts..."

if (Test-Path -LiteralPath $ArchiveDir) {

    $ArchiveItems = Get-ChildItem `
        -LiteralPath $ArchiveDir `
        -Force

    if ($ArchiveItems) {

        $ArchiveItems |
            Remove-Item `
                -Recurse `
                -Force `
                -ErrorAction Stop

        Write-Host "MSSQL archive artifacts removed successfully."
    }
    else {

        Write-Host "MSSQL archive directory is already empty."
    }
}
else {

    Write-Host "MSSQL archive directory not found. Nothing to remove."
}

# =====================================
# CLEAN FAILED ARTIFACTS
# =====================================

Write-Host ""
Write-Host "Cleaning MSSQL failed artifacts..."

if (Test-Path -LiteralPath $FailedDir) {

    $FailedItems = Get-ChildItem `
        -LiteralPath $FailedDir `
        -Force

    if ($FailedItems) {

        $FailedItems |
            Remove-Item `
                -Recurse `
                -Force `
                -ErrorAction Stop

        Write-Host "MSSQL failed artifacts removed successfully."
    }
    else {

        Write-Host "MSSQL failed directory is already empty."
    }
}
else {

    Write-Host "MSSQL failed directory not found. Nothing to remove."
}

# =====================================
# VALIDATION
# =====================================

Write-Host ""
Write-Host "Validating MSSQL load artifacts cleanup..."
Write-Host ""

if (Test-Path -LiteralPath $HistoryFile) {
    throw "MSSQL data load history still exists after cleanup."
}

if (Test-Path -LiteralPath $ArchiveDir) {

    $RemainingArchiveItems = Get-ChildItem `
        -LiteralPath $ArchiveDir `
        -Force

    if ($RemainingArchiveItems) {
        throw "MSSQL archive artifacts still exist after cleanup."
    }
}

if (Test-Path -LiteralPath $FailedDir) {

    $RemainingFailedItems = Get-ChildItem `
        -LiteralPath $FailedDir `
        -Force

    if ($RemainingFailedItems) {
        throw "MSSQL failed artifacts still exist after cleanup."
    }
}

Write-Host "Data load history cleanup validated successfully."
Write-Host "Archive cleanup validated successfully."
Write-Host "Failed artifacts cleanup validated successfully."
Write-Host "Incoming source files preserved."

Write-Host ""
Write-Host "====================================="
Write-Host "MSSQL LOAD ARTIFACTS CLEANUP SUCCESSFUL"
Write-Host "====================================="
Write-Host ""

exit 0