$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "VALIDATING MONGODB CLEANUP"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$MongoHome = Join-Path $PROJECT_ROOT "databases\mongodb"
$MongodExe = Join-Path $MongoHome "server\bin\mongod.exe"

$TerraformDir = Join-Path $PROJECT_ROOT "terraform\mongodb"

$ServiceName = "MongoDBAutomation"

# =====================================
# READ CLEANUP MODE
# =====================================

$CleanupMode = $env:CLEANUP_MODE

if ([string]::IsNullOrWhiteSpace($CleanupMode)) {
    throw "CLEANUP_MODE environment variable is not set."
}

$CleanupMode = $CleanupMode.Trim().ToUpperInvariant()

$AllowedCleanupModes = @(
    "PRESERVE_DATA",
    "DELETE_DATA"
)

if ($CleanupMode -notin $AllowedCleanupModes) {
    throw "Invalid CLEANUP_MODE: $CleanupMode"
}

# =====================================
# READ CONFIG
# =====================================

$ConfigFile = Join-Path $PROJECT_ROOT "config\windows\mongodb.conf"

if (!(Test-Path -LiteralPath $ConfigFile)) {
    throw "Config file not found: $ConfigFile"
}

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

$MongoPort = $Config["MONGODB_PORT"]

if (-not $MongoPort) {
    throw "MONGODB_PORT not found in mongodb.conf"
}

Write-Host "Project Root : $PROJECT_ROOT"
Write-Host "Mongo Home   : $MongoHome"
Write-Host "Cleanup Mode : $CleanupMode"
Write-Host "MongoDB Port : $MongoPort"
Write-Host ""

# =====================================
# VALIDATION RESULT TRACKING
# =====================================

$ValidationErrors = @()

function Add-ValidationError {

    param (
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    $script:ValidationErrors += $Message

    Write-Host "FAILED : $Message"
}

function Confirm-PathAbsent {

    param (
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    if (Test-Path -LiteralPath $Path) {

        Add-ValidationError "$Description still exists: $Path"
    }
    else {

        Write-Host "PASSED : $Description is absent."
    }
}

# =====================================
# VALIDATE PROJECT-MANAGED PROCESS
# =====================================

Write-Host "Validating project-managed MongoDB processes..."
Write-Host ""

$ExpectedMongodPath = [System.IO.Path]::GetFullPath($MongodExe)

$MongoProcesses = Get-CimInstance Win32_Process `
    -Filter "Name='mongod.exe'" `
    -ErrorAction SilentlyContinue

$ProjectProcesses = @()

foreach ($Process in $MongoProcesses) {

    if (-not $Process.ExecutablePath) {
        continue
    }

    try {

        $ActualProcessPath = [System.IO.Path]::GetFullPath(
            $Process.ExecutablePath
        )

        if (
            $ActualProcessPath.Equals(
                $ExpectedMongodPath,
                [System.StringComparison]::OrdinalIgnoreCase
            )
        ) {

            $ProjectProcesses += $Process
        }
    }
    catch {
        continue
    }
}

if ($ProjectProcesses.Count -gt 0) {

    foreach ($Process in $ProjectProcesses) {

        Add-ValidationError `
            "Project-managed mongod process is still running. PID: $($Process.ProcessId)"
    }
}
else {

    Write-Host "PASSED : No project-managed mongod process is running."
}

Write-Host ""
# =====================================
# VALIDATE PROJECT-MANAGED SERVICE
# =====================================

Write-Host "Validating project-managed MongoDB service..."
Write-Host ""

$Service = Get-CimInstance Win32_Service `
    -Filter "Name='$ServiceName'" `
    -ErrorAction SilentlyContinue

if ($Service) {

    Write-Host "MongoDBAutomation service still exists."
    Write-Host "Service Path : $($Service.PathName)"
    Write-Host ""

    $IsProjectService = $false

    if ($Service.PathName) {

        $NormalizedServicePath = $Service.PathName.Trim()

        if (
            $NormalizedServicePath.StartsWith(
                "`"$ExpectedMongodPath`"",
                [System.StringComparison]::OrdinalIgnoreCase
            ) -or
            $NormalizedServicePath.StartsWith(
                $ExpectedMongodPath,
                [System.StringComparison]::OrdinalIgnoreCase
            )
        ) {
            $IsProjectService = $true
        }
    }

    if ($IsProjectService) {

        Add-ValidationError `
            "Project-managed MongoDB service still exists after cleanup."
    }
    else {

        Write-Host "PASSED : MongoDBAutomation service exists but is not owned by this project."
        Write-Host "         External service was not targeted."
    }
}
else {

    Write-Host "PASSED : Project-managed MongoDB service does not exist."
}

Write-Host ""
# =====================================
# VALIDATE PRESERVE DATA MODE
# =====================================

if ($CleanupMode -eq "PRESERVE_DATA") {

    Write-Host "Validating PRESERVE_DATA cleanup..."
    Write-Host ""

    $ServerPath = Join-Path $MongoHome "server"
    $MongoshPath = Join-Path $MongoHome "mongosh"
    $DataPath = Join-Path $MongoHome "data"
    $LogsPath = Join-Path $MongoHome "logs"
    $ConfigPath = Join-Path $MongoHome "config"

    Confirm-PathAbsent `
        -Path $ServerPath `
        -Description "MongoDB server deployment"

    Confirm-PathAbsent `
        -Path $MongoshPath `
        -Description "mongosh deployment"

    Confirm-PathAbsent `
        -Path $LogsPath `
        -Description "MongoDB runtime logs"

    Confirm-PathAbsent `
        -Path $ConfigPath `
        -Description "MongoDB runtime configuration"

    if (Test-Path -LiteralPath $ServerPath) {

        if (Test-Path -LiteralPath $DataPath) {

            Write-Host "PASSED : MongoDB data directory is preserved."
        }
        else {

            Add-ValidationError `
                "MongoDB data directory was not preserved: $DataPath"
        }
    }
    else {

        Write-Host "INFO   : MongoDB server directory not found. Skipping data directory check."
    }

    Write-Host ""

    $MongoZip = Join-Path $MongoHome "mongodb.zip"
    $MongoshZip = Join-Path $MongoHome "mongosh.zip"

    if (Test-Path -LiteralPath $MongoZip) {
        Write-Host "PASSED : MongoDB ZIP cache is preserved."
    }
    else {
        Write-Host "INFO   : MongoDB ZIP cache does not exist."
    }

    if (Test-Path -LiteralPath $MongoshZip) {
        Write-Host "PASSED : mongosh ZIP cache is preserved."
    }
    else {
        Write-Host "INFO   : mongosh ZIP cache does not exist."
    }
}

# =====================================
# VALIDATE DELETE DATA MODE
# =====================================

elseif ($CleanupMode -eq "DELETE_DATA") {

    Write-Host "Validating DELETE_DATA cleanup..."
    Write-Host ""

    Confirm-PathAbsent `
        -Path $MongoHome `
        -Description "Complete project-managed MongoDB deployment"
}

Write-Host ""

# =====================================
# VALIDATE TERRAFORM RUNTIME STATE
# =====================================

Write-Host "Validating MongoDB Terraform runtime state..."
Write-Host ""

$TerraformWorkingDir = Join-Path $TerraformDir ".terraform"

$TerraformState = Join-Path `
    $TerraformDir `
    "terraform.tfstate"

$TerraformStateBackup = Join-Path `
    $TerraformDir `
    "terraform.tfstate.backup"

Confirm-PathAbsent `
    -Path $TerraformWorkingDir `
    -Description "Terraform working directory"

Confirm-PathAbsent `
    -Path $TerraformState `
    -Description "Terraform state file"

Confirm-PathAbsent `
    -Path $TerraformStateBackup `
    -Description "Terraform state backup"

# =====================================
# FINAL RESULT
# =====================================

Write-Host ""

if ($ValidationErrors.Count -gt 0) {

    Write-Host "====================================="
    Write-Host "MONGODB CLEANUP VALIDATION FAILED"
    Write-Host "====================================="
    Write-Host ""

    Write-Host "Validation Errors:"
    Write-Host ""

    foreach ($ValidationError in $ValidationErrors) {

        Write-Host " - $ValidationError"
    }

    Write-Host ""

    exit 1
}

Write-Host "====================================="
Write-Host "MONGODB CLEANUP VALIDATION SUCCESSFUL"
Write-Host "====================================="
Write-Host ""
Write-Host "Cleanup Mode : $CleanupMode"
Write-Host "MongoDB Port : $MongoPort"
Write-Host ""

exit 0