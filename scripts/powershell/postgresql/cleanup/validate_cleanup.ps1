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

$TerraformDirectory = Join-Path $ProjectRoot "terraform\postgresql"

$TerraformState = Join-Path $TerraformDirectory "terraform.tfstate"

$TerraformStateBackup = Join-Path $TerraformDirectory "terraform.tfstate.backup"

$TerraformLockFile = Join-Path $TerraformDirectory ".terraform.tfstate.lock.info"

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
Write-Log "POSTGRESQL CLEANUP VALIDATION"
Write-Log "======================================="
Write-Log ""

Write-Log "Project Root : $ProjectRoot"
Write-Log "Cleanup Mode : $cleanupMode"

# =====================================================
# VALIDATE CLEANUP MODE
# =====================================================

if ($cleanupMode -notin @("PRESERVE_DATA", "DELETE_DATA")) {
    throw "Invalid CLEANUP_MODE: $cleanupMode. Allowed values: PRESERVE_DATA or DELETE_DATA"
}

# =====================================================
# VALIDATE POSTGRESQL PROCESS
# =====================================================

Write-Log "Checking automation-managed PostgreSQL process..."

$postgresProcesses = Get-CimInstance Win32_Process -Filter "Name='postgres.exe'" |
    Where-Object {
        $_.ExecutablePath -and
        $_.ExecutablePath -like "$PgBin\*"
    }

if ($postgresProcesses) {
    throw "Automation-managed PostgreSQL process is still running"
}

Write-Log "PostgreSQL process validation passed."

# =====================================================
# VALIDATE WINDOWS SERVICE
# =====================================================

Write-Log "Checking Windows service: $ServiceName"

$ServiceObject = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($ServiceObject) {

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

    if ($ServiceBinaryPath -ne "") {

        $NormalizedServicePath = (Resolve-Path $ServiceBinaryPath -ErrorAction SilentlyContinue).Path

        if (-not $NormalizedServicePath) {
            $NormalizedServicePath = $ServiceBinaryPath.ToLower()
        }

        $NormalizedProjectRoot = $ProjectRoot.ToLower()

        if ($NormalizedServicePath -like "$NormalizedProjectRoot*") {

            throw "Cleanup validation failed: Project PostgreSQL service still exists: $ServiceName"
        }
    }
}

Write-Log "Windows service validation passed."

if ($cleanupMode -eq "PRESERVE_DATA") {

    Write-Log ""
    Write-Log "Validating PRESERVE_DATA cleanup..."

    if (Test-Path $PgBin) {
        throw "Cleanup validation failed: PostgreSQL bin directory still exists."
    }

    Write-Log "PASS: PostgreSQL bin directory removed."

    if (Test-Path $PgLib) {
        throw "Cleanup validation failed: PostgreSQL lib directory still exists."
    }

    Write-Log "PASS: PostgreSQL lib directory removed."

    if (Test-Path $PgShare) {
        throw "Cleanup validation failed: PostgreSQL share directory still exists."
    }

    Write-Log "PASS: PostgreSQL share directory removed."

    if (Test-Path $PgData) {
        Write-Log "PASS: PostgreSQL data directory preserved."
    }
    else {
        Write-Log "INFO: PostgreSQL data directory does not exist."
    }
}

elseif ($cleanupMode -eq "DELETE_DATA") {

    Write-Log ""
    Write-Log "Validating DELETE_DATA cleanup..."

    if (Test-Path $PgRoot) {
        throw "Cleanup validation failed: PostgreSQL deployment directory still exists."
    }

    Write-Log "PASS: Entire PostgreSQL deployment removed."
}

# =====================================================
# VALIDATE TERRAFORM STATE
# =====================================================

Write-Log ""
Write-Log "Validating Terraform state cleanup..."

if (Test-Path $TerraformState) {
    throw "Cleanup validation failed: terraform.tfstate still exists."
}

Write-Log "PASS: terraform.tfstate removed."

if (Test-Path $TerraformStateBackup) {
    throw "Cleanup validation failed: terraform.tfstate.backup still exists."
}

Write-Log "PASS: terraform.tfstate.backup removed."

if (Test-Path $TerraformLockFile) {
    throw "Cleanup validation failed: Terraform state lock file still exists."
}

Write-Log "PASS: Terraform state lock file removed."

# =====================================================
# SUCCESS
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL CLEANUP VALIDATION PASSED"
Write-Log "======================================="
Write-Log ""

Write-Log "Cleanup Mode : $cleanupMode"
Write-Log "Status       : SUCCESS"

exit 0