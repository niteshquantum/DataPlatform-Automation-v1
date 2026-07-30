$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "PREPARING MSSQL INSTALLATION MEDIA"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

# =====================================
# PATHS
# =====================================

$DownloadDir = Join-Path $PROJECT_ROOT "databases\mssql\downloads"
$MediaDir    = Join-Path $PROJECT_ROOT "databases\mssql\media"

$Bootstrapper = Join-Path $DownloadDir "SQL2022-SSEI-Dev.exe"

# =====================================
# VALIDATE BOOTSTRAPPER
# =====================================

if (!(Test-Path $Bootstrapper)) {
    throw "SQL Server bootstrapper not found.`n$Bootstrapper"
}

# =====================================
# CREATE MEDIA DIRECTORY
# =====================================

if (!(Test-Path $MediaDir)) {

    New-Item `
        -ItemType Directory `
        -Path $MediaDir `
        -Force | Out-Null

}

# =====================================
# EXISTING ISO
# =====================================

$ExistingIso = Get-ChildItem `
    -Path $MediaDir `
    -Filter *.iso `
    -ErrorAction SilentlyContinue

if ($ExistingIso) {

    Write-Host "[OK] SQL Server ISO already exists."
    Write-Host $ExistingIso.FullName
    exit 0

}

# =====================================
# START BOOTSTRAPPER
# =====================================

Write-Host ""
Write-Host "Launching SQL Server bootstrapper..."
Write-Host ""

Start-Process $Bootstrapper

Write-Host ""
Write-Host "======================================================="
Write-Host "COMPLETE THE FOLLOWING IN MICROSOFT SETUP"
Write-Host "======================================================="
Write-Host ""
Write-Host "Edition      : Developer"
Write-Host "Action       : Download Media"
Write-Host "Media Type   : ISO"
Write-Host "Download To  :"
Write-Host "    $MediaDir"
Write-Host ""
Write-Host "When the download finishes,"
Write-Host "return to this PowerShell window"
Write-Host "and press ENTER."
Write-Host ""

Read-Host

# =====================================
# VERIFY ISO
# =====================================

$Iso = Get-ChildItem `
    -Path $MediaDir `
    -Filter *.iso `
    -ErrorAction SilentlyContinue

if (!$Iso) {

    throw "SQL Server ISO was not found in:`n$MediaDir"

}

Write-Host ""
Write-Host "[OK] SQL Server installation media verified."
Write-Host ""
Write-Host "ISO:"
Write-Host $Iso.FullName
Write-Host ""

exit 0