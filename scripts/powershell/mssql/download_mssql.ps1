$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "DOWNLOADING MSSQL SERVER"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

# =====================================
# DOWNLOAD DIRECTORY
# =====================================

$DownloadDir = Join-Path $PROJECT_ROOT "databases\mssql\downloads"

if (!(Test-Path $DownloadDir)) {
    New-Item -ItemType Directory -Path $DownloadDir -Force | Out-Null
}

# =====================================
# INSTALLER
# =====================================

$Installer = Join-Path $DownloadDir "SQL2022-SSEI-Dev.exe"

if (Test-Path $Installer) {

    Write-Host "SQL Server installer already exists."
    Write-Host "Location : $Installer"
    Write-Host ""

}
else {

    # =====================================
    # DOWNLOAD
    # =====================================

    $DownloadUrl = "https://download.microsoft.com/download/c/c/9/cc9c6797-383c-4b24-8920-dc057c1de9d3/SQL2022-SSEI-Dev.exe"

    Write-Host "Downloading SQL Server Developer Edition..."
    Write-Host ""

    Invoke-WebRequest `
        -Uri $DownloadUrl `
        -OutFile $Installer `
        -UseBasicParsing

    if (!(Test-Path $Installer)) {
        throw "SQL Server download failed."
    }

    Write-Host ""
    Write-Host "====================================="
    Write-Host "DOWNLOAD COMPLETED"
    Write-Host "Installer : $Installer"
    Write-Host "====================================="
    Write-Host ""

}


# =====================================
# PREPARE INSTALLATION MEDIA
# =====================================

Write-Host ""
Write-Host "Preparing SQL Server installation media..."
Write-Host ""

& "$PROJECT_ROOT\scripts\powershell\mssql\prepare_mssql_media.ps1"

if ($LASTEXITCODE -ne 0) {
    throw "SQL Server installation media preparation failed."
}

Write-Host ""
Write-Host "[SUCCESS] SQL Server download completed."
Write-Host ""

exit 0