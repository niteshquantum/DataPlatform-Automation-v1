$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "==================================="
Write-Host "STARTING MONGODB"
Write-Host "==================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

$MongoHome = "$PROJECT_ROOT\databases\mongodb"
$MongodExe = "$MongoHome\server\bin\mongod.exe"
$DataPath = "$MongoHome\data"
$LogPath = "$MongoHome\logs\mongodb.log"

# =====================================
# READ CONFIG
# =====================================

$ConfigFile = "$PROJECT_ROOT\config\windows\mongodb.conf"

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

Write-Host "PROJECT_ROOT : $PROJECT_ROOT"
Write-Host "Mongo Home   : $MongoHome"
Write-Host "mongod.exe   : $MongodExe"
Write-Host "Host         : $MongoHost"
Write-Host "Port         : $MongoPort"
Write-Host ""

# =====================================
# NORMALIZE EXPECTED PATHS
# =====================================

$ExpectedMongodPath = [System.IO.Path]::GetFullPath($MongodExe)

function Resolve-ServiceExecutablePath {
    param([string]$ServicePathName)

    if ([string]::IsNullOrWhiteSpace($ServicePathName)) {
        return $null
    }

    $ServiceExecutableMatch = [regex]::Match(
        $ServicePathName.Trim(),
        '(?i)^(?:"(?<quotedPath>[^"]+?\.exe)"|(?<unquotedPath>.+?\.exe))(?=\s|$)'
    )

    if (-not $ServiceExecutableMatch.Success) {
        return $null
    }

    $ServiceExecutable = if ($ServiceExecutableMatch.Groups['quotedPath'].Success) {
        $ServiceExecutableMatch.Groups['quotedPath'].Value
    }
    else {
        $ServiceExecutableMatch.Groups['unquotedPath'].Value
    }

    try {
        return [System.IO.Path]::GetFullPath($ServiceExecutable)
    }
    catch {
        return $null
    }
}

function Get-ManagedMongoServiceCommand {
    return '"{0}" --dbpath "{1}" --logpath "{2}" --logappend --bind_ip "{3}" --port {4} --service' -f `
        $MongodExe, $DataPath, $LogPath, $MongoHost, $MongoPort
}

function Test-MongoPathWritable {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }

    $ProbePath = Join-Path $Path ".mongodb-write-test-$PID.tmp"

    try {
        [System.IO.File]::WriteAllText($ProbePath, '')
    }
    finally {
        Remove-Item -LiteralPath $ProbePath -Force -ErrorAction SilentlyContinue
    }
}

function Test-ManagedMongoStartupPrerequisites {
    param([string]$ServiceName)

    if (-not (Test-Path -LiteralPath $MongodExe)) {
        throw "mongod.exe not found: $MongodExe"
    }

    Test-MongoPathWritable -Path $DataPath
    Test-MongoPathWritable -Path (Split-Path -Parent $LogPath)

    $ServiceAccount = Get-CimInstance `
        Win32_Service `
        -Filter "Name='$ServiceName'" `
        -ErrorAction Stop

    if ([string]::IsNullOrWhiteSpace($ServiceAccount.StartName)) {
        throw "Managed MongoDB service '$ServiceName' does not have a service account."
    }

    $StaleProcesses = Get-CimInstance Win32_Process -Filter "Name='mongod.exe'" -ErrorAction Stop |
        Where-Object {
            $_.ExecutablePath -and
            [System.IO.Path]::GetFullPath($_.ExecutablePath).Equals(
                $ExpectedMongodPath,
                [System.StringComparison]::OrdinalIgnoreCase
            )
        }

    if ($StaleProcesses) {
        throw "A stale managed mongod.exe process is still running."
    }

    $PortConflict = Get-NetTCPConnection `
        -LocalPort $MongoPort `
        -State Listen `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if ($PortConflict) {
        throw "Port $MongoPort is already in use before starting the managed MongoDB service."
    }
}

function Invoke-MongoDirectStartupDiagnostics {
    $DiagnosticStdOut = Join-Path $env:TEMP "mongodb-direct-startup-$PID.stdout.log"
    $DiagnosticStdErr = Join-Path $env:TEMP "mongodb-direct-startup-$PID.stderr.log"

    Remove-Item -LiteralPath $DiagnosticStdOut, $DiagnosticStdErr -Force -ErrorAction SilentlyContinue

    Write-Host "MONGODB DIRECT STARTUP DIAGNOSTICS"

    try {
        $DiagnosticProcess = Start-Process `
            -FilePath $MongodExe `
            -ArgumentList @(
                '--dbpath', $DataPath,
                '--logpath', $LogPath,
                '--logappend',
                '--bind_ip', $MongoHost,
                '--port', $MongoPort
            ) `
            -RedirectStandardOutput $DiagnosticStdOut `
            -RedirectStandardError $DiagnosticStdErr `
            -PassThru `
            -WindowStyle Hidden

        if (-not $DiagnosticProcess.WaitForExit(10000)) {
            Stop-Process -Id $DiagnosticProcess.Id -Force -ErrorAction SilentlyContinue
            $DiagnosticProcess.WaitForExit()
        }

        Write-Host "Direct mongod.exe exit code: $($DiagnosticProcess.ExitCode)"

        if (Test-Path -LiteralPath $DiagnosticStdOut) {
            Write-Host "DIRECT MONGOD STDOUT:"
            Get-Content -LiteralPath $DiagnosticStdOut
        }

        if (Test-Path -LiteralPath $DiagnosticStdErr) {
            Write-Host "DIRECT MONGOD STDERR:"
            Get-Content -LiteralPath $DiagnosticStdErr
        }
    }
    finally {
        Remove-Item -LiteralPath $DiagnosticStdOut, $DiagnosticStdErr -Force -ErrorAction SilentlyContinue
    }
}

function Write-ManagedServiceStartupDiagnostics {
    param(
        [string]$Name,
        [string]$ServicePathName
    )

    Write-Host ""
    Write-Host "MONGODB SERVICE STARTUP DIAGNOSTICS"
    & sc.exe qc $Name
    & sc.exe queryex $Name
    Get-Service -Name $Name -ErrorAction SilentlyContinue | Format-List Name, Status, StartType
    Get-CimInstance Win32_Service -Filter "Name='$Name'" -ErrorAction SilentlyContinue |
        Format-List Name, State, Status, ExitCode, ServiceSpecificExitCode, ProcessId, StartName, PathName

    Get-WinEvent -FilterHashtable @{
        LogName = 'System'
        ProviderName = 'Service Control Manager'
        StartTime = (Get-Date).AddMinutes(-5)
    } -ErrorAction SilentlyContinue |
        Where-Object { $_.Message -match [regex]::Escape($Name) } |
        Select-Object -First 10 TimeCreated, Id, LevelDisplayName, Message |
        Format-List

    Get-WinEvent -FilterHashtable @{
        LogName = 'Application'
        StartTime = (Get-Date).AddMinutes(-5)
    } -ErrorAction SilentlyContinue |
        Where-Object { $_.ProviderName -match 'Mongo' -or $_.Message -match 'mongod|mongodb' } |
        Select-Object -First 20 TimeCreated, Id, ProviderName, LevelDisplayName, Message |
        Format-List

    $LogPathMatch = [regex]::Match(
        $ServicePathName,
        '(?i)--logpath\s+(?:"(?<quotedPath>[^"]+)"|(?<unquotedPath>\S+))'
    )

    if ($LogPathMatch.Success) {
        $ServiceLogPath = if ($LogPathMatch.Groups['quotedPath'].Success) {
            $LogPathMatch.Groups['quotedPath'].Value
        }
        else {
            $LogPathMatch.Groups['unquotedPath'].Value
        }

        if (Test-Path -LiteralPath $ServiceLogPath) {
            Write-Host "LAST MONGODB LOG ENTRIES:"
            Get-Content -LiteralPath $ServiceLogPath -Tail 100
        }
    }
}

function Stop-StaleManagedMongoProcesses {
    param(
        [string]$ServicePathName,
        [string]$FallbackExecutablePath
    )

    $ServiceExecutable = Resolve-ServiceExecutablePath -ServicePathName $ServicePathName

    if (-not $ServiceExecutable) {
        $ServiceExecutable = [System.IO.Path]::GetFullPath($FallbackExecutablePath)
    }

    Get-CimInstance Win32_Process -Filter "Name='mongod.exe'" -ErrorAction Stop |
        Where-Object {
            $_.ExecutablePath -and
            [System.IO.Path]::GetFullPath($_.ExecutablePath).Equals(
                $ServiceExecutable,
                [System.StringComparison]::OrdinalIgnoreCase
            )
        } |
        ForEach-Object {
            Write-Host "Stopping stale managed mongod process (PID $($_.ProcessId)) before service reconfiguration."
            Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop
        }
}

# =====================================
# CHECK IF ALREADY RUNNING
# =====================================

Write-Host "Checking if MongoDB is already running on port $MongoPort..."

$Listener = Get-NetTCPConnection `
    -LocalPort $MongoPort `
    -State Listen `
    -ErrorAction SilentlyContinue |
    Select-Object -First 1

if ($Listener) {

    $OwnerProcessId = $Listener.OwningProcess

    Write-Host ""
    Write-Host "Port $MongoPort is in LISTEN state"
    Write-Host "Listener PID : $OwnerProcessId"

    $OwnerProcessInfo = Get-CimInstance `
        Win32_Process `
        -Filter "ProcessId=$OwnerProcessId" `
        -ErrorAction SilentlyContinue

    $IsProjectOwned = $false
    $ActualPath = $null

    if ($OwnerProcessInfo -and $OwnerProcessInfo.ExecutablePath) {
        $ActualPath = [System.IO.Path]::GetFullPath($OwnerProcessInfo.ExecutablePath)
        Write-Host "Listener Process : $($OwnerProcessInfo.Name)"
        Write-Host "Listener Path    : $ActualPath"
    }

    # =====================================
    # DURABLE SERVICE OWNERSHIP CHECK (CROSS-WORKSPACE)
    # =====================================

    if (-not $IsProjectOwned) {

        $ServiceName = "MongoDBAutomation"

        $ServiceInfo = Get-CimInstance `
            Win32_Service `
            -Filter "Name='$ServiceName'" `
            -ErrorAction SilentlyContinue

        if ($ServiceInfo) {

            $ServiceExe = Resolve-ServiceExecutablePath -ServicePathName $ServiceInfo.PathName

            if ($ActualPath -and $ServiceExe) {
                if ($ActualPath.Equals($ServiceExe, [System.StringComparison]::OrdinalIgnoreCase)) {
                    $IsProjectOwned = $true
                }
            }

            if (-not $IsProjectOwned -and $OwnerProcessId -eq $ServiceInfo.ProcessId) {
                $IsProjectOwned = $true
            }
        }
    }

    # =====================================
    # CURRENT WORKSPACE FALLBACK
    # =====================================

    if (-not $IsProjectOwned -and $ActualPath) {
        if ($ActualPath.Equals($ExpectedMongodPath, [System.StringComparison]::OrdinalIgnoreCase)) {
            $IsProjectOwned = $true
        }
    }

    if (-not $IsProjectOwned) {

        Write-Host ""
        Write-Host "======================================="
        Write-Host "FOREIGN PROCESS LISTENING ON PORT $MongoPort"
        Write-Host "======================================="
        Write-Host "Expected (current workspace) : $ExpectedMongodPath"

        if ($ServiceInfo) {
            Write-Host "Durable service              : $ServiceName"
            Write-Host "Service path                 : $($ServiceInfo.PathName)"
        }

        if ($OwnerProcessInfo) {
            Write-Host "Actual process               : $($OwnerProcessInfo.ExecutablePath)"
            Write-Host "PID                          : $($OwnerProcessInfo.ProcessId)"
            Write-Host "Name                         : $($OwnerProcessInfo.Name)"
        }
        else {
            Write-Host "Actual process               : Unable to resolve executable path"
            Write-Host "PID                          : $OwnerProcessId"
        }

        Write-Host ""
        Write-Host "Action   : Aborting start. Foreign process will not be altered."
        Write-Host "======================================="
        Write-Host ""

        throw "Foreign process detected on MongoDB port $MongoPort. Expected project-managed mongod at: $ExpectedMongodPath"
    }

    Write-Host ""
    Write-Host "Project-managed MongoDB already running on port $MongoPort"
    Write-Host ""

    exit 0
}

# =====================================
# CHECK FOR DURABLE SERVICE (FRESH WORKSPACE)
# =====================================

$ServiceName = "MongoDBAutomation"
$ServiceDisplayName = "MongoDB Automation Service"

$ServiceInfo = Get-Service `
    -Name $ServiceName `
    -ErrorAction SilentlyContinue

if ($ServiceInfo) {

    Write-Host ""
    Write-Host "Durable managed service detected: $ServiceName"
    Write-Host "Service status : $($ServiceInfo.Status)"

    $ServiceConfiguration = Get-CimInstance `
        Win32_Service `
        -Filter "Name='$ServiceName'" `
        -ErrorAction Stop

    $ServiceExecutable = Resolve-ServiceExecutablePath -ServicePathName $ServiceConfiguration.PathName

    $ServicePortMatch = [regex]::Match(
        $ServiceConfiguration.PathName,
        '(?i)--port(?:\s+|=)(?<port>\d+)'
    )

    $ServiceNeedsPortUpdate = -not $ServicePortMatch.Success -or
        [int]$ServicePortMatch.Groups['port'].Value -ne [int]$MongoPort
    $ServiceHasLogAppend = $ServiceConfiguration.PathName -match '(?i)(?:^|\s)--logappend(?:\s|$)'
    $ServiceHasService = $ServiceConfiguration.PathName -match '(?i)(?:^|\s)--service(?:\s|$)'
    $ServiceUsesCurrentWorkspace = $ServiceExecutable -and
        $ServiceExecutable.Equals($ExpectedMongodPath, [System.StringComparison]::OrdinalIgnoreCase) -and
        $ServiceConfiguration.PathName -match [regex]::Escape($DataPath) -and
        $ServiceConfiguration.PathName -match [regex]::Escape($LogPath)
    $ServiceNeedsRecreation = -not $ServiceUsesCurrentWorkspace -or
        $ServiceNeedsPortUpdate -or -not $ServiceHasLogAppend -or -not $ServiceHasService

    if ($ServiceNeedsRecreation) {
        if ($ServiceNeedsPortUpdate -and $ServicePortMatch.Success) {
            $ServicePort = [int]$ServicePortMatch.Groups['port'].Value
            Write-Host "Managed service port ($ServicePort) differs from configured port ($MongoPort). Updating the managed service configuration."
        }
        elseif (-not $ServiceHasLogAppend) {
            Write-Host "Managed service is missing --logappend. Updating the managed service configuration."
        }

        if ($ServiceInfo.Status -eq "Running") {
            Stop-Service -Name $ServiceName -Force -ErrorAction Stop
            $ServiceInfo.WaitForStatus("Stopped", (New-TimeSpan -Seconds 30))
        }

        Stop-StaleManagedMongoProcesses `
            -ServicePathName $ServiceConfiguration.PathName `
            -FallbackExecutablePath $ExpectedMongodPath

        & sc.exe delete $ServiceName | Out-Null

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to remove managed MongoDB service '$ServiceName'."
        }

        for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
            $ServiceCheck = Get-CimInstance `
                Win32_Service `
                -Filter "Name='$ServiceName'" `
                -ErrorAction SilentlyContinue

            if (-not $ServiceCheck) {
                break
            }

            Start-Sleep -Seconds 1
        }

        if (Get-CimInstance Win32_Service -Filter "Name='$ServiceName'" -ErrorAction SilentlyContinue) {
            throw "Managed MongoDB service '$ServiceName' could not be fully removed."
        }

        & $MongodExe `
            --dbpath "$DataPath" `
            --logpath "$LogPath" `
            --logappend `
            --bind_ip "$MongoHost" `
            --port "$MongoPort" `
            --serviceName "$ServiceName" `
            --serviceDisplayName "$ServiceDisplayName" `
            --install

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install managed MongoDB service '$ServiceName'."
        }

        & sc.exe config $ServiceName start= auto | Out-Null

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to configure managed MongoDB service '$ServiceName' for automatic startup."
        }

        $ServiceInfo = Get-Service -Name $ServiceName -ErrorAction Stop
        $ServiceConfiguration = Get-CimInstance `
            Win32_Service `
            -Filter "Name='$ServiceName'" `
            -ErrorAction Stop
    }

    if ($ServiceInfo.Status -eq "Running") {
        Write-Host "Service reports running but port $MongoPort is not listening."
        Write-Host "Waiting briefly for port to become ready..."
        Start-Sleep -Seconds 5

        $PortCheck = netstat -ano | Select-String ":$MongoPort"
        if ($PortCheck) {
            Write-Host "Port $MongoPort is now listening."
            exit 0
        }

        throw "Managed MongoDB service is running but port $MongoPort is not reachable."
    }

    if ($ServiceInfo.Status -ne "Stopped") {
        throw "Managed MongoDB service '$ServiceName' is in unexpected state: $($ServiceInfo.Status). Expected Stopped."
    }

    Write-Host "Starting managed MongoDB service..."
    Write-Host ""

    try {
        Test-ManagedMongoStartupPrerequisites -ServiceName $ServiceName

        Start-Service `
            -Name $ServiceName `
            -ErrorAction Stop
    }
    catch {
        Write-ManagedServiceStartupDiagnostics `
            -Name $ServiceName `
            -ServicePathName $ServiceConfiguration.PathName
        Invoke-MongoDirectStartupDiagnostics
        throw
    }

    Write-Host "Waiting for MongoDB service to start..."

    $ServiceStarted = $false

    for ($i = 1; $i -le 30; $i++) {

        $Svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

        if ($Svc -and $Svc.Status -eq "Running") {
            $ServiceStarted = $true
            break
        }

        Start-Sleep -Seconds 1
    }

    if (-not $ServiceStarted) {

        $Svc = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

        Write-ManagedServiceStartupDiagnostics `
            -Name $ServiceName `
            -ServicePathName $ServiceConfiguration.PathName
        Invoke-MongoDirectStartupDiagnostics

        if ($Svc -and $Svc.Status -ne "Running") {
            throw "Managed MongoDB service failed to start. Current status: $($Svc.Status)"
        }

        throw "Managed MongoDB service did not report Running within timeout."
    }

    Write-Host ""
    Write-Host "Managed MongoDB service started successfully."
    Write-Host ""

    # Wait for port
    $Started = $false

    for ($i = 1; $i -le 30; $i++) {

        $PortCheck = netstat -ano | Select-String ":$MongoPort"

        if ($PortCheck) {
            $Started = $true
            break
        }

        Start-Sleep -Seconds 1
    }

    if (-not $Started) {
        throw "Managed MongoDB service started but port $MongoPort is not listening."
    }

    Write-Host "==================================="
    Write-Host "MONGODB STARTED SUCCESSFULLY (SERVICE)"
    Write-Host "Port : $MongoPort"
    Write-Host "==================================="
    Write-Host ""

    exit 0
}

# =====================================
# VALIDATE
# =====================================

if (!(Test-Path $MongodExe)) {
    throw "mongod.exe not found: $MongodExe"
}

if (!(Test-Path $DataPath)) {
    New-Item -ItemType Directory -Path $DataPath -Force | Out-Null
}

$LogDir = Split-Path $LogPath

if (!(Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# =====================================
# START MONGODB
# =====================================

Start-Process `
    -FilePath $MongodExe `
    -ArgumentList @(
        "--dbpath", $DataPath,
        "--logpath", $LogPath,
        "--bind_ip", $MongoHost,
        "--port", $MongoPort
    ) `
    -WindowStyle Hidden

# =====================================
# WAIT FOR PORT
# =====================================

$Started = $false

for ($i = 1; $i -le 30; $i++) {

    $PortCheck = netstat -ano | Select-String ":$MongoPort"

    if ($PortCheck) {

        $Started = $true
        break
    }

    Start-Sleep -Seconds 1
}

if (-not $Started) {
    throw "MongoDB failed to start on port $MongoPort."
}

Write-Host ""
Write-Host "==================================="
Write-Host "MONGODB STARTED SUCCESSFULLY"
Write-Host "Port : $MongoPort"
Write-Host "==================================="
Write-Host ""

exit 0
