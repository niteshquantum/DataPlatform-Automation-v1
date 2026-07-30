$ErrorActionPreference = "Stop"

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

# =====================================
# CONFIG FILE
# =====================================

$CONFIG_FILE = "$PROJECT_ROOT\config\windows\postgresql.conf"

if (!(Test-Path $CONFIG_FILE)) {
    Write-Error "Config file not found: $CONFIG_FILE"
    exit 1
}

# =====================================
# READ CONFIG
# =====================================

$Config = @{}

Get-Content $CONFIG_FILE | ForEach-Object {

    if ($_ -match "=") {

        $Key, $Value = $_ -split "=", 2
        $Config[$Key.Trim()] = $Value.Trim()

    }

}

$DriverVersion = $Config["POSTGRESQL_DRIVER_VERSION"]

if ([string]::IsNullOrWhiteSpace($DriverVersion)) {
    Write-Error "POSTGRESQL_DRIVER_VERSION not found in postgresql.conf"
    exit 1
}

# =====================================
# DRIVER DIRECTORY
# =====================================

$DriverDir = "$PROJECT_ROOT\tools\drivers"

if (!(Test-Path $DriverDir)) {
    New-Item -ItemType Directory -Path $DriverDir -Force | Out-Null
}

# =====================================
# DRIVER FILE
# =====================================

$JarFile = "$DriverDir\postgresql-$DriverVersion.jar"

if (Test-Path $JarFile) {
    Write-Host "PostgreSQL JDBC Driver already installed."
    exit 0
}

# =====================================
# DOWNLOAD URL
# =====================================

$DownloadUrl = "https://jdbc.postgresql.org/download/postgresql-$DriverVersion.jar"

Write-Host ""
Write-Host "====================================="
Write-Host "DOWNLOADING POSTGRESQL JDBC DRIVER"
Write-Host "====================================="
Write-Host "Version : $DriverVersion"
Write-Host "URL     : $DownloadUrl"
Write-Host ""

Invoke-WebRequest `
    -Uri $DownloadUrl `
    -OutFile $JarFile `
    -UseBasicParsing

# =====================================
# VALIDATE DOWNLOAD
# =====================================

if (!(Test-Path $JarFile)) {
    Write-Error "PostgreSQL JDBC Driver download failed."
    exit 1
}

Write-Host ""
Write-Host "====================================="
Write-Host "POSTGRESQL JDBC DRIVER INSTALLED"
Write-Host "====================================="
Write-Host "Driver : $JarFile"
Write-Host "====================================="