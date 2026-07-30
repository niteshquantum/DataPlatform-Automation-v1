$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$mysqlDir  = "$ROOT\databases\mysql"
$serverDir = "$mysqlDir\server"
$dataDir   = "$mysqlDir\data"
$zipFile   = "$mysqlDir\mysql.zip"

$cleanupMode = $env:CLEANUP_MODE

if ([string]::IsNullOrWhiteSpace($cleanupMode)) {
    $cleanupMode = "PRESERVE_DATA"
}

$cleanupMode = $cleanupMode.ToUpper()

Write-Host ""
Write-Host "====================================="
Write-Host "VALIDATING MYSQL CLEANUP"
Write-Host "====================================="
Write-Host ""

Write-Host "Cleanup Mode : $cleanupMode"
Write-Host "MySQL Path   : $mysqlDir"
Write-Host ""

# =====================================
# VALIDATE CLEANUP MODE
# =====================================

if ($cleanupMode -notin @("PRESERVE_DATA", "DELETE_DATA")) {
    throw "Invalid CLEANUP_MODE: $cleanupMode. Allowed values: PRESERVE_DATA or DELETE_DATA"
}

# =====================================
# VALIDATE MYSQL PROCESS
# =====================================

Write-Host "Checking automation-managed MySQL process..."

$mysqlProcesses = Get-CimInstance Win32_Process -Filter "Name='mysqld.exe'" |
    Where-Object {
        $_.ExecutablePath -and
        $_.ExecutablePath -like "$mysqlDir\*"
    }

if ($mysqlProcesses) {
    throw "Automation-managed MySQL process is still running"
}

Write-Host "MySQL process validation passed."

# =====================================
# VALIDATE SERVER DIRECTORY
# =====================================

Write-Host "Checking MySQL server directory..."

if (Test-Path $serverDir) {
    throw "MySQL server directory still exists: $serverDir"
}

Write-Host "MySQL server directory validation passed."

# =====================================
# VALIDATE ZIP FILE
# =====================================

Write-Host "Checking MySQL ZIP file..."

if (Test-Path $zipFile) {
    throw "MySQL ZIP file still exists: $zipFile"
}

Write-Host "MySQL ZIP validation passed."

# =====================================
# VALIDATE DATA DIRECTORY
# =====================================

Write-Host "Checking MySQL data directory..."

if ($cleanupMode -eq "PRESERVE_DATA") {

    if (Test-Path $serverDir) {
        if (!(Test-Path $dataDir)) {
            throw "MySQL data directory was expected to be preserved but was not found: $dataDir"
        }

        Write-Host "MySQL data directory preserved successfully."
    }
    else {
        Write-Host "MySQL server directory not found. Skipping data directory check."
    }
}

if ($cleanupMode -eq "DELETE_DATA") {

    if (Test-Path $dataDir) {
        throw "MySQL data directory still exists: $dataDir"
    }

    Write-Host "MySQL data directory removal validated successfully."
}

Write-Host ""
Write-Host "====================================="
Write-Host "MYSQL CLEANUP VALIDATION SUCCESSFUL"
Write-Host "====================================="
Write-Host ""

exit 0