$ErrorActionPreference = "Stop"

# Project root
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$ProjectRoot = Split-Path $ProjectRoot -Parent

# Read config
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

$LiquibaseVersion = $Config["LIQUIBASE_VERSION"]

if ([string]::IsNullOrWhiteSpace($LiquibaseVersion)) {
Write-Error "LIQUIBASE_VERSION not found in mysql.conf"
exit 1
}


# tools\liquibase path
$LiquibaseDir = Join-Path $ProjectRoot "tools\liquibase"

if (Test-Path "$LiquibaseDir\liquibase.bat") {
    Write-Host "Liquibase already exists."
    exit 0
}

if (!(Test-Path $LiquibaseDir)) {
    New-Item -ItemType Directory -Path $LiquibaseDir -Force | Out-Null
}

$ZipFile = Join-Path $LiquibaseDir "liquibase.zip"

$DownloadUrl = "https://github.com/liquibase/liquibase/releases/download/v$LiquibaseVersion/liquibase-$LiquibaseVersion.zip"

Write-Host "Downloading Liquibase Version $LiquibaseVersion ..."
Write-Host "URL : $DownloadUrl"

Invoke-WebRequest `
-Uri $DownloadUrl `
-OutFile $ZipFile

if (!(Test-Path $ZipFile)) {
Write-Error "Liquibase download failed."
exit 1
}


Expand-Archive $ZipFile $LiquibaseDir -Force

Remove-Item $ZipFile -Force

if (!(Test-Path "$LiquibaseDir\liquibase.bat")) {
Write-Error "Liquibase installation validation failed."
exit 1
}

Write-Host "LiquibaseDir = $LiquibaseDir"
Get-ChildItem $LiquibaseDir
Write-Host "Liquibase downloaded successfully."