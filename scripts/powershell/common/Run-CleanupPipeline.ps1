param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("mysql","mssql","postgresql","mongodb")]
    [string]$Database,

    [Parameter(Mandatory=$false)]
    [ValidateSet(
        "PRESERVE_DATA",
        "DELETE_DATA",
        "RESET_SCHEMA_CONTEXT"
    )]
    [string]$CleanupMode = "PRESERVE_DATA"
)

$ErrorActionPreference = "Stop"

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path


function Write-Log {
    param(
        [string]$Message
    )

    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Output "[$Timestamp] $Message"
}


function Load-Config {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ConfigFile
    )

    if (!(Test-Path $ConfigFile)) {
        throw "Configuration file not found: $ConfigFile"
    }

    $Config = @{}

    foreach ($Line in Get-Content $ConfigFile) {

        $Line = $Line.Trim()

        if ($Line -eq "" -or $Line.StartsWith("#")) {
            continue
        }

        $Parts = $Line.Split("=", 2)

        if ($Parts.Count -eq 2) {
            $Config[$Parts[0].Trim()] = $Parts[1].Trim()
        }
    }

    return $Config
}


# ============================================================
# START
# ============================================================

Write-Log ""
Write-Log "====================================="
Write-Log "CLEANUP ORCHESTRATOR"
Write-Log "====================================="
Write-Log ""

Write-Log "Database     : $Database"
Write-Log "Cleanup Mode : $CleanupMode"
Write-Log "Project Root : $PROJECT_ROOT"
Write-Log ""


$DbLower = $Database.ToLower()


# ============================================================
# LOAD CONFIGURATION
# ============================================================

$CommonConfig = Load-Config `
    "$PROJECT_ROOT\config\cleanup\cleanup.conf"

$OsConfig = Load-Config `
    "$PROJECT_ROOT\config\cleanup\windows\os.conf"

$DbConfig = Load-Config `
    "$PROJECT_ROOT\config\cleanup\windows\$DbLower.conf"


# ============================================================
# SCRIPT PATHS
# ============================================================

$SchemaContextResetScript = Join-Path `
    $PROJECT_ROOT `
    "scripts\powershell\common\Reset-SchemaContext.ps1"


# ============================================================
# RESET SCHEMA CONTEXT ONLY
# ============================================================

if ($CleanupMode -eq "RESET_SCHEMA_CONTEXT") {

    Write-Log ""
    Write-Log "====================================="
    Write-Log "SCHEMA CONTEXT RESET MODE"
    Write-Log "====================================="
    Write-Log ""

    Write-Log "Only generated schema context will be reset."
    Write-Log "Actual database, tables and data will NOT be modified."
    Write-Log ""

    if (!(Test-Path $SchemaContextResetScript)) {

        Write-Log "[ERROR] Reset schema context script not found:"
        Write-Log $SchemaContextResetScript

        exit 1
    }

    & $SchemaContextResetScript `
        -Database $DbLower

    if ($LASTEXITCODE -ne 0) {

        Write-Log ""
        Write-Log "[ERROR] Schema context reset failed."

        exit 1
    }

    Write-Log ""
    Write-Log "====================================="
    Write-Log "SCHEMA CONTEXT RESET COMPLETED"
    Write-Log "====================================="
    Write-Log ""

    Write-Log "Database     : $DbLower"
    Write-Log "Cleanup Mode : $CleanupMode"
    Write-Log "Status       : SUCCESS"
    Write-Log ""

    exit 0
}


# ============================================================
# NORMAL CLEANUP MODE
# ============================================================

$env:CLEANUP_MODE = $CleanupMode


$StopScript = Join-Path `
    $PROJECT_ROOT `
    "scripts\powershell\$DbLower\cleanup\stop_$DbLower.ps1"


$RemoveScriptName = switch ($DbLower) {

    "mysql" {
        "remove_mysql_deployment.ps1"
    }

    "mssql" {
        "remove_mssql.ps1"
    }

    "postgresql" {
        "remove_postgresql.ps1"
    }

    "mongodb" {
        "remove_mongodb.ps1"
    }
}


$RemoveScript = Join-Path `
    $PROJECT_ROOT `
    "scripts\powershell\$DbLower\cleanup\$RemoveScriptName"


$TerraformScriptName = if ($DbLower -eq "mysql") {
    "reset_mysql_terraform_state.ps1"
}
else {
    "reset_terraform_state.ps1"
}


$TerraformScript = Join-Path `
    $PROJECT_ROOT `
    "scripts\powershell\$DbLower\cleanup\$TerraformScriptName"


$XmlCleanupEnabled = $DbConfig.XML_CLEANUP_ENABLED -eq "true"

$XmlScript = $null

if ($XmlCleanupEnabled) {

    $XmlScript = Join-Path `
        $PROJECT_ROOT `
        "scripts\powershell\$DbLower\cleanup\cleanup_$DbLower`_xml.ps1"
}


$ArtifactsScript = Join-Path `
    $PROJECT_ROOT `
    "scripts\powershell\$DbLower\cleanup\cleanup_$DbLower`_load_artifacts.ps1"


$ValidationScript = Join-Path `
    $PROJECT_ROOT `
    "scripts\powershell\$DbLower\cleanup\validate_cleanup.ps1"


$DataCleanupEnabled = `
    $DbConfig.CLEANUP_DATA_ENABLED_WINDOWS -eq "true"

$DataScript = $null


if (
    (
        $DbLower -eq "mysql" -or
        $DbLower -eq "postgresql"
    ) -and
    $DataCleanupEnabled
) {

    $DataScript = Join-Path `
        $PROJECT_ROOT `
        "scripts\powershell\$DbLower\cleanup\cleanup_$DbLower`_data.ps1"
}


$DropDatabaseEnabled = `
    $DbConfig.DROP_DATABASE_ENABLED_WINDOWS -eq "true"

$DropScript = $null


if (
    $DbLower -eq "mssql" -and
    $DropDatabaseEnabled
) {

    $DropScript = Join-Path `
        $PROJECT_ROOT `
        "scripts\powershell\$DbLower\cleanup\drop_$DbLower`_database.ps1"
}


# ============================================================
# BUILD NORMAL CLEANUP STEPS
# ============================================================

$Steps = @()


if ($DropScript) {

    $Steps += @{
        Name   = "DROP DATABASE"
        Script = $DropScript
    }
}


$Steps += @{
    Name   = "STOP SERVICE"
    Script = $StopScript
}


if ($DataScript) {

    $Steps += @{
        Name   = "CLEANUP DATA"
        Script = $DataScript
    }
}


$Steps += @{
    Name   = "REMOVE DEPLOYMENT"
    Script = $RemoveScript
}


$Steps += @{
    Name   = "RESET TERRAFORM"
    Script = $TerraformScript
}


if ($XmlScript) {

    $Steps += @{
        Name   = "CLEANUP XML"
        Script = $XmlScript
    }
}


$Steps += @{
    Name   = "CLEANUP ARTIFACTS"
    Script = $ArtifactsScript
}


$Steps += @{
    Name   = "VALIDATE"
    Script = $ValidationScript
}


# ============================================================
# EXECUTE NORMAL CLEANUP
# ============================================================

$stepNumber = 0


foreach ($step in $Steps) {

    $stepNumber++

    Write-Log ""
    Write-Log "====================================="
    Write-Log "STEP $stepNumber - $($step.Name)"
    Write-Log "====================================="
    Write-Log ""

    if (!(Test-Path $step.Script)) {

        Write-Log "[ERROR] Script not found:"
        Write-Log $step.Script

        exit 1
    }

    & $step.Script


    if ($LASTEXITCODE -ne 0) {

        Write-Log ""
        Write-Log "[ERROR] Step failed: $($step.Name)"

        exit 1
    }
}


# ============================================================
# COMPLETE
# ============================================================

Write-Log ""
Write-Log "====================================="
Write-Log "$($DbLower.ToUpper()) CLEANUP COMPLETED"
Write-Log "====================================="
Write-Log ""

Write-Log "Database     : $DbLower"
Write-Log "Cleanup Mode : $CleanupMode"
Write-Log "Status       : SUCCESS"
Write-Log ""

exit 0