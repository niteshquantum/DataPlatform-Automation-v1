$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)

    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$Timestamp] $Message"
}

function Get-ProjectRoot {

    $Root = Split-Path $PSScriptRoot -Parent
    $Root = Split-Path $Root -Parent
    $Root = Split-Path $Root -Parent
    $Root = Split-Path $Root -Parent

    return $Root
}

# =====================================================
# PROJECT PATHS
# =====================================================

$ProjectRoot = Get-ProjectRoot

$PgBin = Join-Path $ProjectRoot "databases\postgresql\bin"

$PgData = Join-Path $ProjectRoot "databases\postgresql\data"

$PgCtl = Join-Path $PgBin "pg_ctl.exe"

$ConfigFile = Join-Path $ProjectRoot "config\windows\postgresql.conf"

# =====================================================
# START REPORT
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL CLEANUP - STOP"
Write-Log "======================================="
Write-Log ""

Write-Log "Project Root : $ProjectRoot"
Write-Log "PG Bin       : $PgBin"
Write-Log "PG Data      : $PgData"

# =====================================================
# READ CONFIGURATION
# =====================================================

if (!(Test-Path $ConfigFile)) {

    Write-Log "WARNING: PostgreSQL configuration file not found."
    Write-Log "Config File: $ConfigFile"
}
else {

    Write-Log "Reading PostgreSQL configuration..."

    $Config = @{}

    Get-Content $ConfigFile | ForEach-Object {

        if ($_ -match "^([^#=]+)=(.*)$") {

            $Config[$Matches[1].Trim()] = $Matches[2].Trim()
        }
    }

    $PgHost = $Config["POSTGRESQL_HOST"]

    $PgPort = $Config["POSTGRESQL_PORT"]

    Write-Log "Configured Host : $PgHost"
    Write-Log "Configured Port : $PgPort"
}

# =====================================================
# CHECK POSTGRESQL DEPLOYMENT
# =====================================================

if (!(Test-Path $PgBin)) {

    Write-Log "PostgreSQL bin directory does not exist."
    Write-Log "Nothing to stop."

    Write-Log ""
    Write-Log "======================================="
    Write-Log "POSTGRESQL STOP COMPLETED"
    Write-Log "======================================="

    exit 0
}

if (!(Test-Path $PgCtl)) {

    Write-Log "pg_ctl.exe does not exist."
    Write-Log "Nothing to stop."

    Write-Log ""
    Write-Log "======================================="
    Write-Log "POSTGRESQL STOP COMPLETED"
    Write-Log "======================================="

    exit 0
}

if (!(Test-Path $PgData)) {

    Write-Log "PostgreSQL data directory does not exist."
    Write-Log "Nothing to stop."

    Write-Log ""
    Write-Log "======================================="
    Write-Log "POSTGRESQL STOP COMPLETED"
    Write-Log "======================================="

    exit 0
}

if (!(Test-Path (Join-Path $PgData "PG_VERSION"))) {

    Write-Log "PostgreSQL data directory is not initialized."
    Write-Log "Nothing to stop."

    Write-Log ""
    Write-Log "======================================="
    Write-Log "POSTGRESQL STOP COMPLETED"
    Write-Log "======================================="

    exit 0
}

# =====================================================
# CHECK PROJECT POSTGRESQL STATUS
# =====================================================

Write-Log ""
Write-Log "Checking project PostgreSQL status..."

& "$PgCtl" `
    status `
    -D "$PgData" *> $null

$StatusExitCode = $LASTEXITCODE

if ($StatusExitCode -ne 0) {

    Write-Log "Project PostgreSQL is already stopped."
    Write-Log "Nothing to stop."

    Write-Log ""
    Write-Log "======================================="
    Write-Log "POSTGRESQL STOP COMPLETED"
    Write-Log "======================================="

    exit 0
}

Write-Log "Project PostgreSQL is currently running."

# =====================================================
# STOP PROJECT POSTGRESQL
# =====================================================

Write-Log ""
Write-Log "Stopping project PostgreSQL..."

& "$PgCtl" `
    stop `
    -D "$PgData" `
    -m fast `
    -w `
    -t 60

$StopExitCode = $LASTEXITCODE

if ($StopExitCode -ne 0) {

    throw "PostgreSQL stop failed with exit code $StopExitCode."
}

# =====================================================
# VALIDATE POSTGRESQL STOP
# =====================================================

Write-Log ""
Write-Log "Validating PostgreSQL stop..."

& "$PgCtl" `
    status `
    -D "$PgData" *> $null

$FinalStatusExitCode = $LASTEXITCODE

if ($FinalStatusExitCode -eq 0) {

    throw "PostgreSQL is still running after stop operation."
}

Write-Log "Project PostgreSQL stopped successfully."

# =====================================================
# SUCCESS
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL STOP COMPLETED"
Write-Log "======================================="
Write-Log ""

Write-Log "Project Root : $ProjectRoot"
Write-Log "Data Dir     : $PgData"
Write-Log "Status       : STOPPED"

exit 0