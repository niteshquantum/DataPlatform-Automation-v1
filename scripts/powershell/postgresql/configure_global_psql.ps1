$ErrorActionPreference = "Stop"

function Get-ServiceImagePath {
    param([string]$Name)

    $ServiceInfo = Get-CimInstance Win32_Service -Filter "Name='$Name'" -ErrorAction SilentlyContinue
    if ($ServiceInfo -and $ServiceInfo.PathName) {
        return $ServiceInfo.PathName.Trim()
    }

    return $null
}

function Resolve-ServicePsqlPath {
    param([string]$ServiceImagePath)

    if ([string]::IsNullOrWhiteSpace($ServiceImagePath)) {
        return $null
    }

    $PgCtlMatch = [regex]::Match(
        $ServiceImagePath.Trim(),
        '"?(?<path>[A-Za-z]:\\[^"\r\n]*?\\pg_ctl\.exe)"?',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )

    if (-not $PgCtlMatch.Success) {
        return $null
    }

    $PgCtlPath = $PgCtlMatch.Groups['path'].Value.Trim('"')
    if (-not (Test-Path -LiteralPath $PgCtlPath -PathType Leaf)) {
        return $null
    }

    $PsqlPath = Join-Path (Split-Path -Parent $PgCtlPath) "psql.exe"
    if (Test-Path -LiteralPath $PsqlPath -PathType Leaf) {
        return (Resolve-Path -LiteralPath $PsqlPath).Path
    }

    return $null
}

Write-Host ""
Write-Host "====================================="
Write-Host "CONFIGURING GLOBAL PSQL COMMAND"
Write-Host "====================================="
Write-Host ""

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path
$ConfigFile = "$PROJECT_ROOT\config\windows\postgresql.conf"

if (!(Test-Path $ConfigFile)) {
    throw "Config file not found: $ConfigFile"
}

$Config = @{}
Get-Content $ConfigFile | ForEach-Object {
    $Line = $_.Trim()

    if ($Line -and -not $Line.StartsWith("#") -and $Line.Contains("=")) {
        $Key, $Value = $Line.Split("=", 2)
        $Config[$Key.Trim()] = $Value.Trim()
    }
}

$PgHost     = $Config["POSTGRESQL_HOST"]
$PgPort     = $Config["POSTGRESQL_PORT"]
$PgDatabase = $Config["POSTGRESQL_DB"]
$PgUser     = $Config["POSTGRESQL_USER"]
$PgPassword = $Config["POSTGRESQL_PASSWORD"]

if (-not $PgHost) { throw "POSTGRESQL_HOST not found in postgresql.conf" }
if (-not $PgPort) { throw "POSTGRESQL_PORT not found in postgresql.conf" }
if (-not $PgDatabase) { throw "POSTGRESQL_DB not found in postgresql.conf" }
if (-not $PgUser) { throw "POSTGRESQL_USER not found in postgresql.conf" }

$WorkspacePsqlExe = Join-Path $PROJECT_ROOT "databases\postgresql\bin\psql.exe"
$PsqlExe = $null

if (Test-Path -LiteralPath $WorkspacePsqlExe -PathType Leaf) {
    $PsqlExe = (Resolve-Path -LiteralPath $WorkspacePsqlExe).Path
}
else {
    $ServiceName = "PostgreSQLAutomation"
    $ServiceImagePath = Get-ServiceImagePath -Name $ServiceName
    $PsqlExe = Resolve-ServicePsqlPath -ServiceImagePath $ServiceImagePath

    if ($PsqlExe) {
        Write-Host "Resolved psql.exe from existing PostgreSQL service: $PsqlExe"
    }
}

if (-not $PsqlExe) {
    throw "psql.exe not found in workspace: $WorkspacePsqlExe. Unable to resolve it from the PostgreSQLAutomation service."
}

Write-Host "psql.exe : $PsqlExe"
Write-Host "Host     : $PgHost"
Write-Host "Port     : $PgPort"
Write-Host "Database : $PgDatabase"
Write-Host "User     : $PgUser"

$GlobalDirectory = "C:\ProgramData\DatabaseAutomation\postgresql"
if (!(Test-Path $GlobalDirectory)) {
    New-Item -ItemType Directory -Path $GlobalDirectory -Force | Out-Null
}

$SafeDatabaseName = ($PgDatabase -replace '[^A-Za-z0-9]', '_')
$InstanceWrapperName = "psql_${SafeDatabaseName}_${PgPort}.cmd"
$InstanceWrapperPath = Join-Path $GlobalDirectory $InstanceWrapperName
$GlobalCommand = "$GlobalDirectory\psql.cmd"

$CommandContent = @"
@echo off

set "PGPASSWORD=$PgPassword"

"$PsqlExe" ^
--host="$PgHost" ^
--port="$PgPort" ^
--username="$PgUser" ^
--dbname="$PgDatabase" %*

set "PGPASSWORD="
"@

Set-Content -Path $InstanceWrapperPath -Value $CommandContent -Encoding ASCII
Set-Content -Path $GlobalCommand -Value $CommandContent -Encoding ASCII

if (!(Test-Path $GlobalCommand)) {
    throw "Global psql command creation failed"
}

$MachinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
$PathEntries = $MachinePath -split ";"
if ($PathEntries -notcontains $GlobalDirectory) {
    Write-Host ""
    Write-Host "Adding psql command directory to System PATH..."
    $NewPath = $MachinePath.TrimEnd(";") + ";" + $GlobalDirectory
    [Environment]::SetEnvironmentVariable("Path", $NewPath, "Machine")
}
else {
    Write-Host ""
    Write-Host "psql command directory already exists in System PATH"
}

Write-Host ""
Write-Host "====================================="
Write-Host "GLOBAL PSQL CONFIGURED SUCCESSFULLY"
Write-Host "====================================="
Write-Host ""
Write-Host "Command:"
Write-Host "psql"
Write-Host "Instance wrapper:"
Write-Host $InstanceWrapperName
Write-Host ""
Write-Host "Open a NEW CMD before testing."
Write-Host ""

exit 0
