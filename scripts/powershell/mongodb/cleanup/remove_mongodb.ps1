$ErrorActionPreference = "Stop"

. "$PSScriptRoot\MongoDB-CleanupSafety.ps1"
$context = Get-MongoDBCleanupContext
$cleanupMode = if ([string]::IsNullOrWhiteSpace($env:CLEANUP_MODE)) { 'PRESERVE_DATA' } else { $env:CLEANUP_MODE.Trim().ToUpperInvariant() }
if ($cleanupMode -notin @('PRESERVE_DATA', 'DELETE_DATA')) { throw "Invalid CLEANUP_MODE: $cleanupMode" }
if (-not (Test-MongoDBProjectManaged $context)) {
    Write-Host 'No verified project-managed MongoDB deployment was found. External MongoDB resources are untouched.'
    exit 0
}
$service = Get-Service -Name $context.ServiceName -ErrorAction SilentlyContinue
if ($service) {
    if ($service.Status -ne 'Stopped') { throw 'Refusing to remove a running project-managed MongoDB service.' }
    & sc.exe delete $context.ServiceName | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not remove project-managed MongoDB service: $($context.ServiceName)" }
}
if ($cleanupMode -eq 'PRESERVE_DATA') {
    foreach ($path in @((Join-Path $context.InstallDir 'server'), (Join-Path $context.InstallDir 'mongosh'), (Join-Path $context.InstallDir 'logs'), (Join-Path $context.InstallDir 'config'))) { Remove-MongoDBProjectPath -Path $path -Context $context }
    Write-Host 'Project-managed MongoDB deployment was removed; data was preserved.'
} else {
    Remove-MongoDBProjectPath -Path $context.InstallDir -Context $context
    Write-Host 'Project-managed MongoDB deployment and data were removed.'
}
exit 0

Write-Host ""
Write-Host "====================================="
Write-Host "REMOVING PROJECT-MANAGED MONGODB"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$MongoHome = Join-Path $PROJECT_ROOT "databases\mongodb"
$MongodExe = Join-Path $MongoHome "server\bin\mongod.exe"
$MongoshExe = Join-Path $MongoHome "mongosh\bin\mongosh.exe"

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

Write-Host "Project Root : $PROJECT_ROOT"
Write-Host "Mongo Home   : $MongoHome"
Write-Host "Cleanup Mode : $CleanupMode"
Write-Host "Service      : $ServiceName"
Write-Host ""

# =====================================
# SAFETY VALIDATION
# =====================================

$ExpectedMongoHome = [System.IO.Path]::GetFullPath(
    (Join-Path $PROJECT_ROOT "databases\mongodb")
)

$ActualMongoHome = [System.IO.Path]::GetFullPath(
    $MongoHome
)

if (
    -not $ActualMongoHome.Equals(
        $ExpectedMongoHome,
        [System.StringComparison]::OrdinalIgnoreCase
    )
) {
    throw "MongoDB cleanup safety validation failed."
}

$ExpectedMongodPath = [System.IO.Path]::GetFullPath(
    $MongodExe
)

$ExpectedMongoshPath = [System.IO.Path]::GetFullPath(
    $MongoshExe
)

# =====================================
# REMOVE PROJECT-MANAGED SERVICE
# =====================================

Write-Host "Checking project-managed MongoDB service..."
Write-Host ""

$Service = Get-CimInstance Win32_Service `
    -Filter "Name='$ServiceName'" `
    -ErrorAction SilentlyContinue

if ($Service) {

    Write-Host "MongoDBAutomation service found."
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

    if (-not $IsProjectService) {

        Write-Host ""
        Write-Host "WARNING: MongoDBAutomation service exists but is not owned by this project."
        Write-Host "Expected executable:"
        Write-Host "$ExpectedMongodPath"
        Write-Host ""
        Write-Host "Actual service path:"
        Write-Host "$($Service.PathName)"
        Write-Host ""
        Write-Host "Skipping service removal for safety."
        Write-Host ""
    }
    else {

        # =====================================
        # ENSURE SERVICE IS STOPPED
        # =====================================

    if ($Service.State -eq "Running") {

        Write-Host "Project-managed service is still running."
        Write-Host "Stopping service..."

        Stop-Service `
            -Name $ServiceName `
            -Force `
            -ErrorAction Stop

        $ServiceStopped = $false

        for ($i = 1; $i -le 30; $i++) {

            $CurrentService = Get-Service `
                -Name $ServiceName `
                -ErrorAction SilentlyContinue

            if (
                $null -eq $CurrentService -or
                $CurrentService.Status -eq "Stopped"
            ) {
                $ServiceStopped = $true
                break
            }

            Start-Sleep -Seconds 1
        }

        if (-not $ServiceStopped) {
            throw "Project-managed MongoDB service failed to stop."
        }

        Write-Host "Project-managed MongoDB service stopped."
        Write-Host ""
    }
    else {

        Write-Host "Project-managed MongoDB service is already stopped."
        Write-Host ""
    }

        # =====================================
        # DELETE SERVICE
        # =====================================

        Write-Host "Removing project-managed MongoDB service..."

        & sc.exe delete $ServiceName | Out-Null

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to delete project-managed MongoDB service."
        }

        # =====================================
        # WAIT FOR SERVICE REMOVAL
        # =====================================

        $ServiceRemoved = $false

        for ($i = 1; $i -le 30; $i++) {

            $CurrentService = Get-CimInstance Win32_Service `
                -Filter "Name='$ServiceName'" `
                -ErrorAction SilentlyContinue

            if ($null -eq $CurrentService) {

                $ServiceRemoved = $true
                break
            }

            Start-Sleep -Seconds 1
        }

        if (-not $ServiceRemoved) {
            throw "MongoDB service deletion could not be confirmed."
        }

        Write-Host "Project-managed MongoDB service removed successfully."
    }
}
else {

    Write-Host "Project-managed MongoDB service does not exist."
    Write-Host "Nothing to unregister."
}

Write-Host ""

# =====================================
# IDEMPOTENCY CHECK
# =====================================

if (!(Test-Path -LiteralPath $MongoHome)) {

    Write-Host "MongoDB deployment directory does not exist."
    Write-Host "Nothing to remove."
    Write-Host ""

    exit 0
}

# =====================================
# STOP PROJECT-MANAGED MONGOSH PROCESS
# =====================================

Write-Host "Checking project-managed mongosh processes..."
Write-Host ""

$MongoshProcesses = Get-CimInstance Win32_Process `
    -Filter "Name='mongosh.exe'" `
    -ErrorAction SilentlyContinue

$ProjectMongoshFound = $false

foreach ($Process in $MongoshProcesses) {

    if ($Process.ExecutablePath) {

        $ActualProcessPath = [System.IO.Path]::GetFullPath(
            $Process.ExecutablePath
        )

        if (
            $ActualProcessPath.Equals(
                $ExpectedMongoshPath,
                [System.StringComparison]::OrdinalIgnoreCase
            )
        ) {

            $ProjectMongoshFound = $true

            Write-Host "Stopping project-managed mongosh process..."
            Write-Host "PID  : $($Process.ProcessId)"
            Write-Host "Path : $ActualProcessPath"

            Stop-Process `
                -Id $Process.ProcessId `
                -Force `
                -ErrorAction Stop

            Write-Host "Project-managed mongosh process stopped."
            Write-Host ""
        }
    }
}

if (-not $ProjectMongoshFound) {

    Write-Host "No running project-managed mongosh process found."
    Write-Host ""
}

# =====================================
# WAIT FOR MONGOSH PROCESS RELEASE
# =====================================

Start-Sleep -Seconds 2

# =====================================
# VALIDATE MONGOSH PROCESS STOPPED
# =====================================

Write-Host "Validating project-managed mongosh process status..."
Write-Host ""

$RemainingMongoshProcesses = Get-CimInstance Win32_Process `
    -Filter "Name='mongosh.exe'" `
    -ErrorAction SilentlyContinue

foreach ($Process in $RemainingMongoshProcesses) {

    if ($Process.ExecutablePath) {

        $ActualProcessPath = [System.IO.Path]::GetFullPath(
            $Process.ExecutablePath
        )

        if (
            $ActualProcessPath.Equals(
                $ExpectedMongoshPath,
                [System.StringComparison]::OrdinalIgnoreCase
            )
        ) {
            throw "Project-managed mongosh process is still running."
        }
    }
}

Write-Host "Project-managed mongosh process validation passed."
Write-Host ""

# =====================================
# HELPER FUNCTION
# =====================================

function Remove-ProjectPath {

    param (
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    if (Test-Path -LiteralPath $Path) {

        Write-Host "Removing $Description..."
        Write-Host "Path : $Path"

        Remove-Item `
            -LiteralPath $Path `
            -Recurse `
            -Force `
            -ErrorAction Stop

        if (Test-Path -LiteralPath $Path) {
            throw "Failed to remove ${Description}: $Path"
        }

        Write-Host "$Description removed successfully."
    }
    else {

        Write-Host "$Description already absent. Skipping."
    }

    Write-Host ""
}

# =====================================
# PRESERVE DATA MODE
# =====================================

if ($CleanupMode -eq "PRESERVE_DATA") {

    Write-Host "Applying PRESERVE_DATA cleanup..."
    Write-Host ""

    $ServerPath = Join-Path $MongoHome "server"
    $MongoshPath = Join-Path $MongoHome "mongosh"
    $LogsPath = Join-Path $MongoHome "logs"
    $ConfigPath = Join-Path $MongoHome "config"

    Remove-ProjectPath `
        -Path $ServerPath `
        -Description "MongoDB server deployment"

    Remove-ProjectPath `
        -Path $MongoshPath `
        -Description "mongosh deployment"

    Remove-ProjectPath `
        -Path $LogsPath `
        -Description "MongoDB runtime logs"

    Remove-ProjectPath `
        -Path $ConfigPath `
        -Description "MongoDB runtime configuration"

    Write-Host "MongoDB data directory preserved."
    Write-Host "MongoDB download cache preserved."
    Write-Host ""
}

# =====================================
# DELETE DATA MODE
# =====================================

elseif ($CleanupMode -eq "DELETE_DATA") {

    Write-Host "Applying DELETE_DATA cleanup..."
    Write-Host ""

    Remove-ProjectPath `
        -Path $MongoHome `
        -Description "complete project-managed MongoDB deployment"
}

# =====================================
# SUCCESS
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "MONGODB DEPLOYMENT REMOVAL COMPLETE"
Write-Host "====================================="
Write-Host ""
Write-Host "Cleanup Mode : $CleanupMode"
Write-Host ""

exit 0
