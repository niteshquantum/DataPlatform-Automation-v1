$ErrorActionPreference = "Stop"

# Project root
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$ProjectRoot = Split-Path $ProjectRoot -Parent

# Resolve tools root
$ToolsRoot = $env:DATA_PLATFORM_TOOLS_ROOT
if ([string]::IsNullOrWhiteSpace($ToolsRoot)) {
    $ToolsRoot = "C:\Program Files\DataPlatform\tools"
}

# Read config
$ConfigFile = $env:DATA_PLATFORM_CONFIG_FILE
if ([string]::IsNullOrWhiteSpace($ConfigFile)) {
    $CandidateConfigs = @(
        (Join-Path $ProjectRoot "config\windows\mysql.conf"),
        (Join-Path $ProjectRoot "config\windows\mssql.conf"),
        (Join-Path $ProjectRoot "config\windows\postgresql.conf")
    )

    foreach ($Candidate in $CandidateConfigs) {
        if (Test-Path $Candidate) {
            $ConfigFile = $Candidate
            break
        }
    }
}

if ([string]::IsNullOrWhiteSpace($ConfigFile) -or !(Test-Path $ConfigFile)) {
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
$LiquibaseDir = Join-Path $ToolsRoot "liquibase"

if (Test-Path "$LiquibaseDir\liquibase.bat") {
    Write-Host "Liquibase already installed. Skipping installation."
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