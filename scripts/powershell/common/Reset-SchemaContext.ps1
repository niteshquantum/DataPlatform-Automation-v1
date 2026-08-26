param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("mysql", "mongodb", "postgresql", "mssql")]
    [string]$Database
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
# RESET LIQUIBASE CONTEXT
# ============================================================

function Reset-LiquibaseContext {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LiquibasePath
    )

    Write-Log ""
    Write-Log "====================================="
    Write-Log "RESET LIQUIBASE CONTEXT"
    Write-Log "====================================="
    Write-Log ""

    Write-Log "Path : $LiquibasePath"

    if (!(Test-Path $LiquibasePath)) {
        Write-Log "Status : NOT FOUND"
        Write-Log "Action : SKIPPED - Nothing to reset"
        return
    }

    # Remove all generated XML files except master.xml
    $GeneratedXmlFiles = Get-ChildItem `
        -Path $LiquibasePath `
        -Filter "*.xml" `
        -File `
        -Recurse |
        Where-Object { $_.Name -ine "master.xml" }

    if ($GeneratedXmlFiles.Count -eq 0) {

        Write-Log "Generated XML files : NONE"
    }
    else {

        foreach ($XmlFile in $GeneratedXmlFiles) {

            Write-Log "Removing generated XML : $($XmlFile.FullName)"

            Remove-Item `
                -Path $XmlFile.FullName `
                -Force
        }
    }

    # Reset master.xml
    $MasterXml = Join-Path $LiquibasePath "master.xml"

    $CleanMasterContent = @'
<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="
    http://www.liquibase.org/xml/ns/dbchangelog
    http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

</databaseChangeLog>
'@

    Write-Log "Resetting master.xml"

    Set-Content `
        -Path $MasterXml `
        -Value $CleanMasterContent `
        -Encoding UTF8

    Write-Log "Status : RESET SUCCESSFULLY"
}


# ============================================================
# RESET LOAD HISTORY
# ============================================================

function Reset-LoadHistory {
    param(
        [Parameter(Mandatory = $true)]
        [string]$HistoryPath
    )

    Write-Log ""
    Write-Log "====================================="
    Write-Log "RESET LOAD HISTORY"
    Write-Log "====================================="
    Write-Log ""

    Write-Log "Path : $HistoryPath"

    if (!(Test-Path $HistoryPath)) {

        Write-Log "Status : NOT FOUND"
        Write-Log "Action : SKIPPED - Nothing to reset"
        return
    }

    Write-Log "Removing load history"

    Remove-Item `
        -Path $HistoryPath `
        -Force

    Write-Log "Status : RESET SUCCESSFULLY"
}


# ============================================================
# RESET OBJECT REGISTRY
# ============================================================

function Reset-ObjectRegistry {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RegistryPath
    )

    Write-Log ""
    Write-Log "====================================="
    Write-Log "RESET OBJECT REGISTRY"
    Write-Log "====================================="
    Write-Log ""

    Write-Log "Path : $RegistryPath"

    if (!(Test-Path $RegistryPath)) {

        Write-Log "Status : NOT FOUND"
        Write-Log "Action : Creating fresh object registry"
    }
    else {

        Write-Log "Existing object registry found."
        Write-Log "Action : Resetting old object context"
    }

    $RegistryDirectory = Split-Path `
        -Path $RegistryPath `
        -Parent

    if (!(Test-Path $RegistryDirectory)) {

        New-Item `
            -Path $RegistryDirectory `
            -ItemType Directory `
            -Force | Out-Null
    }

    Set-Content `
        -Path $RegistryPath `
        -Value "{}" `
        -Encoding UTF8

    Write-Log "Status : RESET SUCCESSFULLY"
}


# ============================================================
# GENERIC JSON CONTEXT RESET
# ============================================================

function Reset-JsonContext {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(Mandatory = $false)]
        [string]$Content = "{}"
    )

    Write-Log ""
    Write-Log "====================================="
    Write-Log "RESET $Name"
    Write-Log "====================================="
    Write-Log ""

    Write-Log "Path : $FilePath"

    $Directory = Split-Path `
        -Path $FilePath `
        -Parent

    if (!(Test-Path $Directory)) {

        New-Item `
            -Path $Directory `
            -ItemType Directory `
            -Force | Out-Null
    }

    if (Test-Path $FilePath) {

        Write-Log "Existing context found."
        Write-Log "Action : Resetting old context"
    }
    else {

        Write-Log "Status : NOT FOUND"
        Write-Log "Action : Creating fresh context"
    }

    Set-Content `
        -Path $FilePath `
        -Value $Content `
        -Encoding UTF8

    Write-Log "Status : RESET SUCCESSFULLY"
}


# ============================================================
# MONGODB-SPECIFIC RESET CONTEXT
# ============================================================

function Resolve-ProjectResetPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $ResolvedPath = [System.IO.Path]::GetFullPath(
        (Join-Path $PROJECT_ROOT $RelativePath)
    )

    $ProjectRootPrefix = $PROJECT_ROOT.TrimEnd('\') + '\'

    if (-not $ResolvedPath.StartsWith(
        $ProjectRootPrefix,
        [System.StringComparison]::OrdinalIgnoreCase
    )) {
        throw "Refusing to reset path outside PROJECT_ROOT: $RelativePath"
    }

    return $ResolvedPath
}


function Reset-MongoDBContextFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$RelativePath,

        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $FilePath = Resolve-ProjectResetPath -RelativePath $RelativePath
    $Directory = Split-Path -Path $FilePath -Parent

    Write-Log ""
    Write-Log "====================================="
    Write-Log "RESET $Name"
    Write-Log "====================================="
    Write-Log "Path : $FilePath"

    if (!(Test-Path -LiteralPath $Directory)) {
        New-Item -Path $Directory -ItemType Directory -Force | Out-Null
    }

    Set-Content -LiteralPath $FilePath -Value $Content -Encoding UTF8
    Write-Log "Status : RESET SUCCESSFULLY"
}


function Remove-MongoDBContextFileIfPresent {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    $FilePath = Resolve-ProjectResetPath -RelativePath $RelativePath

    Write-Log ""
    Write-Log "====================================="
    Write-Log "RESET $Name"
    Write-Log "====================================="
    Write-Log "Path : $FilePath"

    if (Test-Path -LiteralPath $FilePath) {
        Remove-Item -LiteralPath $FilePath -Force
        Write-Log "Status : REMOVED"
    }
    else {
        Write-Log "Status : NOT FOUND"
        Write-Log "Action : SKIPPED - Nothing to reset"
    }
}


function Reset-MongoDBSchemaContext {
    Reset-MongoDBContextFile -Name "SCHEMA REGISTRY" -RelativePath "metadata\mongodb\schema_registry.json" -Content "{}"
    Reset-MongoDBContextFile -Name "DATATYPE REGISTRY" -RelativePath "metadata\mongodb\datatype_registry.json" -Content "{}"
    Reset-MongoDBContextFile -Name "TABLE SOURCE MAPPING" -RelativePath "metadata\mongodb\table_source_mapping.json" -Content "{}"
    Reset-MongoDBContextFile -Name "CDC STATUS" -RelativePath "metadata\mongodb\cdc_status.json" -Content '{"tables":{}}'

    Remove-MongoDBContextFileIfPresent -Name "LOAD HISTORY" -RelativePath "metadata\data_load_history.jsonl"
}


# ============================================================
# CONFIGURATION
# ============================================================

$DbLower = $Database.ToLower()

$CleanupConfigFile = Join-Path `
    $PROJECT_ROOT `
    "config\cleanup\windows\$DbLower.conf"

$DbConfig = Load-Config $CleanupConfigFile


$DatabaseConfigFile = Join-Path `
    $PROJECT_ROOT `
    "config\windows\$DbLower.conf"

$DatabaseConfig = Load-Config $DatabaseConfigFile


$DatabaseNameKey = switch ($DbLower) {

    "mysql"      { "MYSQL_DB" }
    "mongodb"    { "MONGODB_DATABASE" }
    "postgresql" { "POSTGRESQL_DB" }
    "mssql"      { "MSSQL_DB" }
}


$DatabaseName = $DatabaseConfig[$DatabaseNameKey]

if ([string]::IsNullOrWhiteSpace($DatabaseName)) {
    throw "Database name not found in configuration key: $DatabaseNameKey"
}


# ============================================================
# START
# ============================================================

Write-Log ""
Write-Log "============================================================"
Write-Log "RESET SCHEMA CONTEXT"
Write-Log "============================================================"
Write-Log ""

Write-Log "Database      : $DbLower"
Write-Log "Database Name : $DatabaseName"
Write-Log "Project Root  : $PROJECT_ROOT"

Write-Log ""
Write-Log "Cleanup Config : $CleanupConfigFile"
Write-Log "Database Config: $DatabaseConfigFile"


if ($DbLower -eq "mongodb") {
    Write-Log ""
    Write-Log "MongoDB does not use Liquibase or an object registry in this reset flow."

    Reset-MongoDBSchemaContext

    Write-Log ""
    Write-Log "============================================================"
    Write-Log "SCHEMA CONTEXT RESET COMPLETED"
    Write-Log "============================================================"
    Write-Log ""
    Write-Log "Database      : $DbLower"
    Write-Log "Database Name : $DatabaseName"
    Write-Log "Status        : SUCCESS"
    Write-Log ""
    Write-Log "NOTE: MongoDB service, database, collections, indexes and data were NOT modified."
    Write-Log ""

    exit 0
}


# ============================================================
# RESET LIQUIBASE CONTEXT
# ============================================================

if ($DbConfig.LIQUIBASE_ENABLED -eq "true") {

    $LiquibasePath = Join-Path `
        $PROJECT_ROOT `
        $DbConfig.LIQUIBASE_DIR

    Reset-LiquibaseContext `
        -LiquibasePath $LiquibasePath
}
else {

    Write-Log ""
    Write-Log "Liquibase reset disabled for $DbLower."
}


# ============================================================
# RESET LOAD HISTORY
# ============================================================

if (![string]::IsNullOrWhiteSpace($DbConfig.HISTORY_FILE)) {

    $HistoryPath = Join-Path `
        $PROJECT_ROOT `
        $DbConfig.HISTORY_FILE

    Reset-LoadHistory `
        -HistoryPath $HistoryPath
}


# ============================================================
# RESET OBJECT REGISTRY
# ============================================================

$ObjectRegistryPath = Join-Path `
    $PROJECT_ROOT `
    "metadata\$DbLower\object_registry.json"

Reset-ObjectRegistry `
    -RegistryPath $ObjectRegistryPath


# ============================================================
# RESET SCHEMA REGISTRY
# ============================================================

$SchemaRegistryPath = Join-Path `
    $PROJECT_ROOT `
    "metadata\$DbLower\schema_registry.json"

Reset-JsonContext `
    -Name "SCHEMA REGISTRY" `
    -FilePath $SchemaRegistryPath `
    -Content "{}"


# ============================================================
# RESET TABLE SOURCE MAPPING
# ============================================================

$TableSourceMappingPath = Join-Path `
    $PROJECT_ROOT `
    "metadata\$DbLower\table_source_mapping.json"

Reset-JsonContext `
    -Name "TABLE SOURCE MAPPING" `
    -FilePath $TableSourceMappingPath `
    -Content "{}"


# ============================================================
# RESET CDC STATUS
# ============================================================

$CdcStatusPath = Join-Path `
    $PROJECT_ROOT `
    "metadata\$DbLower\cdc_status.json"

Reset-JsonContext `
    -Name "CDC STATUS" `
    -FilePath $CdcStatusPath `
    -Content '{"tables":{}}'


# ============================================================
# COMPLETE
# ============================================================

Write-Log ""
Write-Log "============================================================"
Write-Log "SCHEMA CONTEXT RESET COMPLETED"
Write-Log "============================================================"
Write-Log ""

Write-Log "Database      : $DbLower"
Write-Log "Database Name : $DatabaseName"
Write-Log "Status        : SUCCESS"

Write-Log ""
Write-Log "NOTE: Actual database, tables and data were NOT modified."
Write-Log ""

exit 0
