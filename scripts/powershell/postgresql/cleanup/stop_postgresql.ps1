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

$PgBin   = Join-Path $ProjectRoot "databases\postgresql\bin"
$PgData  = Join-Path $ProjectRoot "databases\postgresql\data"
$PgCtl   = Join-Path $PgBin "pg_ctl.exe"
$ConfigFile = Join-Path $ProjectRoot "config\windows\postgresql.conf"

# =====================================================
# SERVICE CONFIGURATION
# =====================================================

$ServiceName = "PostgreSQLAutomation"

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
# STOP WINDOWS SERVICE
# =====================================================

Write-Log ""
Write-Log "Checking Windows service: $ServiceName"

$ServiceObject = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($ServiceObject) {

    Write-Log "Windows service found: $ServiceName"

    $ServiceQuery = sc.exe query $ServiceName 2>&1 | Out-String

    if ($ServiceQuery -match "RUNNING") {

        Write-Log "Service is currently running."

        $ServiceConfig = sc.exe qc $ServiceName 2>&1 | Out-String

        $ServiceBinaryPath = ""

        foreach ($Line in $ServiceConfig -split "`r?`n") {

            $Trimmed = $Line.Trim()

            if ($Trimmed -match "^BINARY_PATH_NAME\s*:\s*(.+)$") {

                $ServiceBinaryPath = $Matches[1].Trim()

                if ($ServiceBinaryPath.StartsWith('"') -and $ServiceBinaryPath.EndsWith('"')) {
                    $ServiceBinaryPath = $ServiceBinaryPath.Substring(1, $ServiceBinaryPath.Length - 2)
                }

                break
            }
        }

        if ($ServiceBinaryPath -eq "") {

            throw "Could not determine binary path for service: $ServiceName"
        }

        $NormalizedServicePath = (Resolve-Path $ServiceBinaryPath -ErrorAction SilentlyContinue).Path

        if (-not $NormalizedServicePath) {
            $NormalizedServicePath = $ServiceBinaryPath.ToLower()
        }

        $NormalizedProjectBin = $PgBin.ToLower()

        if ($NormalizedServicePath -like "$NormalizedProjectBin*") {

            Write-Log "Service binary path is within project deployment."
            Write-Log "Service Path: $ServiceBinaryPath"

            Write-Log ""
            Write-Log "Stopping Windows service: $ServiceName"

            Stop-Service -Name $ServiceName -Force

            $ServiceObject.WaitForStatus("Stopped", "00:00:30")

            Write-Log "Windows service stopped successfully."
        }
        else {

            Write-Log "WARNING: Service binary path does not belong to this project."
            Write-Log "Service Path    : $ServiceBinaryPath"
            Write-Log "Project Bin Dir : $PgBin"
            Write-Log "Skipping service stop."
        }
    }
    else {

        Write-Log "Service is not running. Nothing to stop."
    }
}
else {

    Write-Log "Windows service not found: $ServiceName"
    Write-Log "Nothing to stop."
}

# =====================================================
# STOP PROJECT POSTGRESQL PROCESSES
# =====================================================

Write-Log ""
Write-Log "Checking automation-managed PostgreSQL processes..."

$postgresProcesses = Get-CimInstance Win32_Process -Filter "Name='postgres.exe'" |
    Where-Object {
        $_.ExecutablePath -and
        $_.ExecutablePath -ieq (Join-Path $PgBin "postgres.exe")
    }

if ($postgresProcesses) {

    Write-Log "Automation-managed PostgreSQL processes found:"

    foreach ($process in $postgresProcesses) {
        Write-Log "  Stopping PID: $($process.ProcessId) - $($process.ExecutablePath)"
        Stop-Process -Id $process.ProcessId -Force
    }

    Start-Sleep -Seconds 3
}
else {

    Write-Log "No automation-managed PostgreSQL processes found."
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