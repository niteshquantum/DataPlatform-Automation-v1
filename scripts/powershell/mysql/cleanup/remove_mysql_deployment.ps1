$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$mysqlDir = "$ROOT\databases\mysql"
$serverDir = "$mysqlDir\server"
$zipFile = "$mysqlDir\mysql.zip"

Write-Host ""
Write-Host "====================================="
Write-Host "REMOVING MYSQL DEPLOYMENT"
Write-Host "====================================="
Write-Host ""

Write-Host "MySQL Directory : $mysqlDir"
Write-Host ""

# =====================================
# REMOVE MYSQL SERVER
# =====================================

if (Test-Path $serverDir) {

    Write-Host "Removing MySQL server directory..."

    Remove-Item $serverDir -Recurse -Force
}
else {
    Write-Host "MySQL server directory not found."
    Write-Host "Nothing to remove."
}

# =====================================
# REMOVE MYSQL ZIP
# =====================================

if (Test-Path $zipFile) {

    Write-Host ""
    Write-Host "Removing MySQL ZIP file..."

    Remove-Item $zipFile -Force
}
else {
    Write-Host ""
    Write-Host "MySQL ZIP file not found."
    Write-Host "Nothing to remove."
}

# =====================================
# VALIDATE REMOVAL
# =====================================

Write-Host ""
Write-Host "Validating MySQL deployment removal..."

if (Test-Path $serverDir) {
    throw "MySQL server directory still exists: $serverDir"
}

if (Test-Path $zipFile) {
    throw "MySQL ZIP file still exists: $zipFile"
}

Write-Host ""
Write-Host "====================================="
Write-Host "MYSQL DEPLOYMENT REMOVED SUCCESSFULLY"
Write-Host "====================================="
Write-Host ""

exit 0