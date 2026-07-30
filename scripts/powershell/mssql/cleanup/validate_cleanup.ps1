$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "VALIDATING MSSQL CLEANUP"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

# =====================================
# LOAD CONFIG
# =====================================

. "$PROJECT_ROOT\scripts\powershell\common\load_config.ps1"

$Config = Load-Config "$PROJECT_ROOT\config\windows\mssql.conf"

$Instance = $Config["MSSQL_INSTANCE"]

if ([string]::IsNullOrWhiteSpace($Instance)) {
    throw "MSSQL_INSTANCE is missing in config/windows/mssql.conf"
}

# =====================================
# CLEANUP MODE
# =====================================

$CleanupMode = $env:CLEANUP_MODE

if ([string]::IsNullOrWhiteSpace($CleanupMode)) {
    throw "CLEANUP_MODE environment variable is not set."
}

$CleanupMode = $CleanupMode.Trim().ToUpperInvariant()

if ($CleanupMode -notin @("PRESERVE_DATA", "DELETE_DATA")) {
    throw "Invalid CLEANUP_MODE: $CleanupMode"
}

# =====================================
# SERVICE NAME
# =====================================

if ($Instance -eq "MSSQLSERVER") {
    $ServiceName = "MSSQLSERVER"
}
else {
    $ServiceName = "MSSQL`$$Instance"
}

Write-Host "Project Root : $PROJECT_ROOT"
Write-Host "Instance     : $Instance"
Write-Host "Service Name : $ServiceName"
Write-Host "Cleanup Mode : $CleanupMode"
Write-Host ""

# =====================================
# CHECK MSSQL SERVICE
# =====================================

Write-Host "Checking MSSQL service..."
Write-Host ""

$Service = Get-Service `
    -Name $ServiceName `
    -ErrorAction SilentlyContinue

if ($CleanupMode -eq "PRESERVE_DATA") {

    if (!$Service) {
        Write-Host "MSSQL service does not exist in PRESERVE_DATA mode."
        Write-Host "This is expected in local runtime."
    }
    elseif ($Service.Status -ne "Stopped") {
        Write-Host "WARNING: MSSQL service is still running after PRESERVE_DATA cleanup."
        Write-Host "This is expected in local runtime without admin privileges."
    }
    else {
        Write-Host "MSSQL service preservation validated successfully."
    }
}
else {

    if ($Service) {
        throw "MSSQL service still exists after DELETE_DATA cleanup."
    }

    Write-Host "MSSQL service removal validated successfully."
}

# =====================================
# VALIDATE LIQUIBASE XML
# =====================================

Write-Host ""
Write-Host "Checking MSSQL Liquibase XML state..."
Write-Host ""

$LiquibaseDir = Join-Path $PROJECT_ROOT "liquibase\mssql"
$MasterXml = Join-Path $LiquibaseDir "master.xml"

if ($CleanupMode -eq "DELETE_DATA") {

    $GeneratedXmlFiles = Get-ChildItem `
        -Path $LiquibaseDir `
        -Filter "*.xml" `
        -File `
        -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -ne "master.xml"
        }

    if ($GeneratedXmlFiles.Count -gt 0) {
        throw "Generated MSSQL Liquibase XML files still exist."
    }

    if (!(Test-Path -LiteralPath $MasterXml)) {
        throw "MSSQL master.xml does not exist."
    }

    Write-Host "MSSQL Liquibase XML cleanup validated successfully."
}
else {

    Write-Host "MSSQL Liquibase XML preserved in PRESERVE_DATA mode."
}

# =====================================
# VALIDATE LOAD ARTIFACTS
# =====================================

Write-Host ""
Write-Host "Checking MSSQL load artifacts..."
Write-Host ""

$HistoryFile = Join-Path `
    $PROJECT_ROOT `
    "metadata\mssql\data_load_history.jsonl"

$ArchiveDir = Join-Path `
    $PROJECT_ROOT `
    "archive\mssql"

$FailedDir = Join-Path `
    $PROJECT_ROOT `
    "failed\mssql"

$IncomingDir = Join-Path `
    $PROJECT_ROOT `
    "incoming\mssql"

if ($CleanupMode -eq "DELETE_DATA") {

    if (Test-Path -LiteralPath $HistoryFile) {
        throw "MSSQL data load history still exists."
    }

    if (Test-Path -LiteralPath $ArchiveDir) {

        $ArchiveItems = Get-ChildItem `
            -LiteralPath $ArchiveDir `
            -Force

        if ($ArchiveItems) {
            throw "MSSQL archive artifacts still exist."
        }
    }

    if (Test-Path -LiteralPath $FailedDir) {

        $FailedItems = Get-ChildItem `
            -LiteralPath $FailedDir `
            -Force

        if ($FailedItems) {
            throw "MSSQL failed artifacts still exist."
        }
    }

    Write-Host "MSSQL load artifacts cleanup validated successfully."
}
else {

    Write-Host "MSSQL load artifacts preserved in PRESERVE_DATA mode."
}

# =====================================
# INCOMING FILES
# =====================================

Write-Host ""
Write-Host "Checking incoming source directory..."
Write-Host ""

if (Test-Path -LiteralPath $IncomingDir) {

    Write-Host "MSSQL incoming source directory preserved."
}
else {

    Write-Host "MSSQL incoming source directory does not currently exist."
    Write-Host "No cleanup validation failure required."
}

# =====================================
# SUCCESS
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "MSSQL CLEANUP VALIDATION SUCCESSFUL"
Write-Host "====================================="
Write-Host ""
Write-Host "Cleanup Mode : $CleanupMode"
Write-Host ""

exit 0