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

$PgRoot  = Join-Path $ProjectRoot "databases\postgresql"
$PgBin   = Join-Path $PgRoot "bin"
$PgLib   = Join-Path $PgRoot "lib"
$PgShare = Join-Path $PgRoot "share"
$PgData  = Join-Path $PgRoot "data"

$ServiceName = "PostgreSQLAutomation"

# =====================================================
# READ CLEANUP MODE
# =====================================================

$cleanupMode = $env:CLEANUP_MODE

if ([string]::IsNullOrWhiteSpace($cleanupMode)) {
    $cleanupMode = "PRESERVE_DATA"
}

$cleanupMode = $cleanupMode.ToUpper()

# =====================================================
# START REPORT
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL CLEANUP - REMOVE DEPLOYMENT"
Write-Log "======================================="
Write-Log ""

Write-Log "Project Root : $ProjectRoot"
Write-Log "PG Root      : $PgRoot"
Write-Log "Cleanup Mode : $cleanupMode"

# =====================================================
# VALIDATE CLEANUP MODE
# =====================================================

if ($cleanupMode -notin @("PRESERVE_DATA", "DELETE_DATA")) {
    throw "Invalid CLEANUP_MODE: $cleanupMode. Allowed values: PRESERVE_DATA or DELETE_DATA"
}

# =====================================================
# CHECK POSTGRESQL ROOT
# =====================================================

if (!(Test-Path $PgRoot)) {

    Write-Log ""
    Write-Log "PostgreSQL deployment directory does not exist."
    Write-Log "Nothing to remove."

    Write-Log ""
    Write-Log "======================================="
    Write-Log "POSTGRESQL REMOVAL COMPLETED"
    Write-Log "======================================="

    exit 0
}

# =====================================================
# REMOVE WINDOWS SERVICE
# =====================================================

Write-Log ""
Write-Log "Checking Windows service: $ServiceName"

$ServiceObject = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($ServiceObject) {

    Write-Log "Windows service found: $ServiceName"

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

        Write-Log "WARNING: Could not determine binary path for service: $ServiceName"
        Write-Log "Skipping service removal to avoid removing unrelated services."
    }
    else {

        $NormalizedServicePath = (Resolve-Path $ServiceBinaryPath -ErrorAction SilentlyContinue).Path

        if (-not $NormalizedServicePath) {
            $NormalizedServicePath = $ServiceBinaryPath.ToLower()
        }

        $NormalizedProjectRoot = $ProjectRoot.ToLower()

        if ($NormalizedServicePath -like "$NormalizedProjectRoot*") {

            Write-Log "Service binary path is within project deployment."
            Write-Log "Service Path: $ServiceBinaryPath"

            Write-Log ""
            Write-Log "Stopping service before removal: $ServiceName"

            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue

            $ServiceObject.WaitForStatus("Stopped", "00:00:10")

            Write-Log ""
            Write-Log "Removing Windows service: $ServiceName"

            sc.exe delete $ServiceName 2>&1 | Out-Null

            $ServiceAfterDelete = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

            if ($ServiceAfterDelete) {
                throw "Failed to remove Windows service: $ServiceName"
            }

            Write-Log "Windows service removed successfully."
        }
        else {

            Write-Log "WARNING: Service binary path does not belong to this project."
            Write-Log "Service Path    : $ServiceBinaryPath"
            Write-Log "Project Root    : $ProjectRoot"
            Write-Log "Skipping service removal."
        }
    }
}
else {

    Write-Log "Windows service not found: $ServiceName"
    Write-Log "Nothing to remove."
}

# =====================================================
# PRESERVE DATA MODE
# =====================================================

if ($cleanupMode -eq "PRESERVE_DATA") {

    Write-Log ""
    Write-Log "PRESERVE_DATA mode selected."
    Write-Log "PostgreSQL data directory will be preserved."

    $DeploymentDirectories = @(
        $PgBin,
        $PgLib,
        $PgShare
    )

    foreach ($Directory in $DeploymentDirectories) {

        if (Test-Path $Directory) {

            Write-Log "Removing directory: $Directory"

            Remove-Item `
                -Path $Directory `
                -Recurse `
                -Force

            if (Test-Path $Directory) {
                throw "Failed to remove directory: $Directory"
            }

            Write-Log "Removed successfully: $Directory"
        }
        else {
            Write-Log "Directory does not exist. Skipping: $Directory"
        }
    }

    if (Test-Path $PgData) {

        Write-Log ""
        Write-Log "Data directory preserved successfully."
        Write-Log "Preserved Data: $PgData"
    }
    else {

        Write-Log ""
        Write-Log "Data directory does not exist."
        Write-Log "Nothing available to preserve."
    }
}

# =====================================================
# DELETE DATA MODE
# =====================================================

elseif ($cleanupMode -eq "DELETE_DATA") {

    Write-Log ""
    Write-Log "DELETE_DATA mode selected."
    Write-Log "Entire project PostgreSQL deployment will be removed."

    Write-Log "Removing directory: $PgRoot"

    Remove-Item `
        -Path $PgRoot `
        -Recurse `
        -Force

    if (Test-Path $PgRoot) {
        throw "Failed to remove PostgreSQL deployment directory: $PgRoot"
    }

    Write-Log "Entire PostgreSQL deployment removed successfully."
}

# =====================================================
# FINAL VALIDATION
# =====================================================

Write-Log ""
Write-Log "Validating PostgreSQL deployment removal..."

if ($cleanupMode -eq "PRESERVE_DATA") {

    if (Test-Path $PgBin) {
        throw "PostgreSQL bin directory still exists."
    }

    if (Test-Path $PgLib) {
        throw "PostgreSQL lib directory still exists."
    }

    if (Test-Path $PgShare) {
        throw "PostgreSQL share directory still exists."
    }

    Write-Log "Deployment binaries removed successfully."

    if (Test-Path $PgData) {
        Write-Log "PostgreSQL data directory remains preserved."
    }
}

elseif ($cleanupMode -eq "DELETE_DATA") {

    if (Test-Path $PgRoot) {
        throw "PostgreSQL deployment directory still exists."
    }

    Write-Log "PostgreSQL deployment and data removed successfully."
}

# =====================================================
# SUCCESS
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL REMOVAL COMPLETED"
Write-Log "======================================="
Write-Log ""

Write-Log "Cleanup Mode : $cleanupMode"

if ($cleanupMode -eq "PRESERVE_DATA") {
    Write-Log "Data Status  : PRESERVED"
}
else {
    Write-Log "Data Status  : DELETED"
}

exit 0