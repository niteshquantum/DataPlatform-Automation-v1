$ErrorActionPreference = "Stop"

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

# =====================================
# CONFIG FILE
# =====================================

$CONFIG_FILE = "$PROJECT_ROOT\config\windows\mysql.conf"

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

$DriverVersion = $Config["MYSQL_DRIVER_VERSION"]

if ([string]::IsNullOrWhiteSpace($DriverVersion)) {
    Write-Error "MYSQL_DRIVER_VERSION not found in mysql.conf"
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

$JarFile = "$DriverDir\mysql-connector-j-$DriverVersion.jar"

if (Test-Path $JarFile) {
    Write-Host "MySQL Connector already installed."
    exit 0
}

# =====================================
# DOWNLOAD URL
# =====================================

$DownloadUrl = "https://repo1.maven.org/maven2/com/mysql/mysql-connector-j/$DriverVersion/mysql-connector-j-$DriverVersion.jar"

Write-Host ""
Write-Host "====================================="
Write-Host "DOWNLOADING MYSQL JDBC DRIVER"
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
    Write-Error "MySQL JDBC Driver download failed."
    exit 1
}

Write-Host ""
Write-Host "====================================="
Write-Host "MYSQL JDBC DRIVER INSTALLED"
Write-Host "====================================="
Write-Host "Driver : $JarFile"
Write-Host "====================================="