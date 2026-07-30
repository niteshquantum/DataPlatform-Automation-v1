
$ErrorActionPreference = "Stop"

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

$ConfigFile = "$PROJECT_ROOT\config\windows\mongodb.conf"

Write-Host ""
Write-Host "====================================="
Write-Host "CONFIGURING GLOBAL MONGOSH COMMAND"
Write-Host "====================================="
Write-Host ""

if (!(Test-Path $ConfigFile)) {
    throw "Config file not found: $ConfigFile"
}

# READ CONFIG

$Config = @{}

Get-Content $ConfigFile | ForEach-Object {

    $Line = $_.Trim()

    if (
        $Line -and
        -not $Line.StartsWith("#") -and
        $Line.Contains("=")
    ) {
        $Key, $Value = $Line.Split("=", 2)
        $Config[$Key.Trim()] = $Value.Trim()
    }
}

$MongoHost = $Config["MONGODB_HOST"]
$MongoPort = $Config["MONGODB_PORT"]

if (-not $MongoHost) {
    throw "MONGODB_HOST not found in mongodb.conf"
}

if (-not $MongoPort) {
    throw "MONGODB_PORT not found in mongodb.conf"
}

# FIND MONGOSH.EXE

$MongoshExe = Get-ChildItem `
    -Path "$PROJECT_ROOT\databases\mongodb\mongosh" `
    -Filter "mongosh.exe" `
    -Recurse `
    -File |
    Select-Object -First 1

if ($null -eq $MongoshExe) {
    throw "mongosh.exe not found"
}

$MongoshPath = $MongoshExe.FullName

Write-Host "mongosh.exe : $MongoshPath"
Write-Host "Host        : $MongoHost"
Write-Host "Port        : $MongoPort"

# CREATE GLOBAL COMMAND

$GlobalDirectory = "C:\ProgramData\DatabaseAutomation\mongodb"
$GlobalCommand = "$GlobalDirectory\mongosh.cmd"

if (!(Test-Path $GlobalDirectory)) {
    New-Item `
        -ItemType Directory `
        -Path $GlobalDirectory `
        -Force | Out-Null
}

$CommandContent = @"
@echo off
"$MongoshPath" --host "$MongoHost" --port "$MongoPort" %*
"@

Set-Content `
    -Path $GlobalCommand `
    -Value $CommandContent `
    -Encoding ASCII

if (!(Test-Path $GlobalCommand)) {
    throw "Global mongosh command creation failed"
}

# ADD TO MACHINE PATH

$MachinePath = [Environment]::GetEnvironmentVariable(
    "Path",
    "Machine"
)

$PathEntries = $MachinePath -split ";"

if ($PathEntries -notcontains $GlobalDirectory) {

    Write-Host ""
    Write-Host "Adding mongosh command directory to System PATH..."

    $NewPath = $MachinePath.TrimEnd(";") + ";" + $GlobalDirectory

    [Environment]::SetEnvironmentVariable(
        "Path",
        $NewPath,
        "Machine"
    )
}
else {
    Write-Host ""
    Write-Host "mongosh command directory already exists in System PATH"
}

Write-Host ""
Write-Host "====================================="
Write-Host "GLOBAL MONGOSH CONFIGURED SUCCESSFULLY"
Write-Host "====================================="
Write-Host ""
Write-Host "Command:"
Write-Host "mongosh"
Write-Host ""
Write-Host "Open a NEW CMD before testing."
Write-Host ""

exit 0
