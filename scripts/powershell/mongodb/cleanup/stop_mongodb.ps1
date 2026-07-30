$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "STOPPING PROJECT-MANAGED MONGODB"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$MongoHome = Join-Path $PROJECT_ROOT "databases\mongodb"
$MongodExe = Join-Path $MongoHome "server\bin\mongod.exe"

$ServiceName = "MongoDBAutomation"

# =====================================
# READ CONFIG
# =====================================

$ConfigFile = Join-Path $PROJECT_ROOT "config\windows\mongodb.conf"

if (!(Test-Path $ConfigFile)) {
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

$MongoHost = $Config["MONGODB_HOST"]
$MongoPort = $Config["MONGODB_PORT"]

if (-not $MongoPort) {
    throw "MONGODB_PORT not found in mongodb.conf"
}

Write-Host "Project Root : $PROJECT_ROOT"
Write-Host "Mongo Home   : $MongoHome"
Write-Host "mongod.exe   : $MongodExe"
Write-Host "Host         : $MongoHost"
Write-Host "Port         : $MongoPort"
Write-Host "Service      : $ServiceName"
Write-Host ""

# =====================================
# NORMALIZE EXPECTED EXECUTABLE PATH
# =====================================

$ExpectedMongodPath = [System.IO.Path]::GetFullPath($MongodExe)

# =====================================
# STOP PROJECT-MANAGED WINDOWS SERVICE
# =====================================

Write-Host "Checking project-managed MongoDB service..."

$Service = Get-CimInstance Win32_Service `
    -Filter "Name='$ServiceName'" `
    -ErrorAction SilentlyContinue

if ($Service) {

    Write-Host "MongoDB service found."

    $ServicePath = $Service.PathName

    Write-Host "Service Path : $ServicePath"

    $IsProjectService = $false

    if ($ServicePath) {

        $NormalizedServicePath = $ServicePath.Trim()

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

        if ($Service.State -eq "Running") {

            Write-Host "Stopping project-managed MongoDB service..."

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

            Write-Host "Project-managed MongoDB service stopped successfully."
        }
        else {
            Write-Host "Project-managed MongoDB service is already stopped."
        }
    }
    else {

        Write-Host ""
        Write-Host "WARNING: MongoDBAutomation service exists but does not belong to this project."
        Write-Host "Service will NOT be stopped."
        Write-Host ""
    }
}
else {
    Write-Host "Project-managed MongoDB service does not exist."
}

Write-Host ""

# =====================================
# STOP PROJECT-MANAGED STANDALONE PROCESS
# =====================================

Write-Host "Checking project-managed standalone MongoDB processes..."

$ProjectMongoProcesses = @()

$MongoProcesses = Get-CimInstance Win32_Process `
    -Filter "Name='mongod.exe'" `
    -ErrorAction SilentlyContinue

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
            $ProjectMongoProcesses += $Process
        }
    }
    catch {
        Write-Host "Unable to inspect mongod process PID: $($Process.ProcessId)"
    }
}

if ($ProjectMongoProcesses.Count -eq 0) {

    Write-Host "No project-managed standalone MongoDB process is running."
}
else {

    foreach ($Process in $ProjectMongoProcesses) {

        Write-Host "Stopping project-managed mongod process..."
        Write-Host "PID  : $($Process.ProcessId)"
        Write-Host "Path : $($Process.ExecutablePath)"

        Stop-Process `
            -Id $Process.ProcessId `
            -Force `
            -ErrorAction Stop
    }

    Start-Sleep -Seconds 3

    Write-Host "Project-managed standalone MongoDB process stopped successfully."
}

# =====================================
# FINAL PROJECT PROCESS VALIDATION
# =====================================

Write-Host ""
Write-Host "Validating project-managed MongoDB shutdown..."

$RemainingProjectProcesses = @()

$RemainingMongoProcesses = Get-CimInstance Win32_Process `
    -Filter "Name='mongod.exe'" `
    -ErrorAction SilentlyContinue

foreach ($Process in $RemainingMongoProcesses) {

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
            $RemainingProjectProcesses += $Process
        }
    }
    catch {
        continue
    }
}

if ($RemainingProjectProcesses.Count -gt 0) {
    throw "Project-managed MongoDB process is still running."
}

Write-Host ""
Write-Host "====================================="
Write-Host "PROJECT-MANAGED MONGODB STOPPED"
Write-Host "====================================="
Write-Host ""
Write-Host "System-installed MongoDB instances were not targeted."
Write-Host "MongoDB Port : $MongoPort"
Write-Host ""

exit 0