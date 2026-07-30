$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path $PSScriptRoot -Parent
$ProjectRoot = Split-Path $ProjectRoot -Parent

$ConfigFile = Join-Path $ProjectRoot "config\windows\mssql.conf"

if (!(Test-Path $ConfigFile)) {
Write-Error "Config file not found: $ConfigFile"
exit 1
}

$Config = @{}

Get-Content $ConfigFile | ForEach-Object {
if ($_ -match "=") {
$Key, $Value = $_ -split "=", 2
$Config[$Key.Trim()] = $Value.Trim()
}
}

$DriverVersion = $Config["MSSQL_DRIVER_VERSION"]

if ([string]::IsNullOrWhiteSpace($DriverVersion)) {
Write-Error "MSSQL_DRIVER_VERSION not found in mssql.conf"
exit 1
}

$DriverDir = Join-Path $ProjectRoot "tools\drivers"

if (!(Test-Path $DriverDir)) {
New-Item -ItemType Directory -Path $DriverDir -Force | Out-Null
}

$JarFile = Join-Path $DriverDir "mssql-jdbc-$DriverVersion.jre11.jar"

if (Test-Path $JarFile) {
Write-Host "MSSQL JDBC Driver already exists."
exit 0
}

$DownloadUrl = "https://repo1.maven.org/maven2/com/microsoft/sqlserver/mssql-jdbc/$DriverVersion.jre11/mssql-jdbc-$DriverVersion.jre11.jar"

Write-Host "Downloading MSSQL JDBC Driver..."
Write-Host "URL : $DownloadUrl"

Invoke-WebRequest -Uri $DownloadUrl -OutFile $JarFile -UseBasicParsing


if (!(Test-Path $JarFile)) {
Write-Error "Driver download failed."
exit 1
}

Write-Host "MSSQL JDBC Driver downloaded successfully."
