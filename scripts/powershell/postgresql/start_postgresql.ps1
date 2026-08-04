$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

function Get-ProjectRoot {
    $Root = Split-Path $PSScriptRoot -Parent
    $Root = Split-Path $Root -Parent
    $Root = Split-Path $Root -Parent
    return $Root
}

function Get-ServiceImagePath {
    param([string]$Name)

    $Info = Get-CimInstance Win32_Service -Filter "Name='$Name'" -ErrorAction SilentlyContinue
    if ($Info -and $Info.PathName) {
        return $Info.PathName.Trim()
    }

    return $null
}

function Resolve-ServicePgCtlPath {
    param([string]$ServiceImagePath)

    if ([string]::IsNullOrWhiteSpace($ServiceImagePath)) {
        return $null
    }

    $match = [regex]::Match(
        $ServiceImagePath.Trim(),
        '"?(?<path>[A-Za-z]:\\[^"\r\n]*?\\pg_ctl\.exe)"?',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )

    if (-not $match.Success) {
        return $null
    }

    $path = $match.Groups['path'].Value.Trim('"')
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        return $path
    }

    return $null
}

function Resolve-ServicePsqlPath {
    param([string]$ServiceImagePath)

    $pgCtlPath = Resolve-ServicePgCtlPath -ServiceImagePath $ServiceImagePath
    if (-not $pgCtlPath) {
        return $null
    }

    $psqlPath = Join-Path (Split-Path -Parent $pgCtlPath) "psql.exe"
    if (Test-Path -LiteralPath $psqlPath -PathType Leaf) {
        return (Resolve-Path -LiteralPath $psqlPath).Path
    }

    return $null
}

$ProjectRoot = Get-ProjectRoot
$ConfigFile = Join-Path $ProjectRoot "config\windows\postgresql.conf"
$LogDirectory = Join-Path $ProjectRoot "outputs\logs"

if (!(Test-Path $ConfigFile)) {
    throw "Configuration file not found: $ConfigFile"
}

if (!(Test-Path $LogDirectory)) {
    New-Item -ItemType Directory -Path $LogDirectory -Force | Out-Null
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

$PgHost = $Config["POSTGRESQL_HOST"]
$ExpectedPort = [int]$Config["POSTGRESQL_PORT"]
$PgDatabase = $Config["POSTGRESQL_DB"]
$PgUser = if ([string]::IsNullOrWhiteSpace($Config["POSTGRESQL_USER"])) { "postgres" } else { $Config["POSTGRESQL_USER"] }

if ([string]::IsNullOrWhiteSpace($PgHost)) {
    throw "POSTGRESQL_HOST missing."
}

if ([string]::IsNullOrWhiteSpace($PgDatabase)) {
    throw "POSTGRESQL_DB missing."
}

if ($ExpectedPort -le 0) {
    throw "Invalid POSTGRESQL_PORT."
}

$ServiceName = "PostgreSQLAutomation"

# =====================================
# PATHS
# =====================================

$PgBin  = Join-Path $ProjectRoot "databases\postgresql\bin"
$PgData = Join-Path $ProjectRoot "databases\postgresql\data"
$PgLog  = Join-Path $LogDirectory "postgresql.log"
$PgCtl  = Join-Path $PgBin "pg_ctl.exe"
$Psql   = Join-Path $PgBin "psql.exe"

$ServiceImagePath = Get-ServiceImagePath -Name $ServiceName

if (-not (Test-Path $Psql)) {
    $ServicePsqlPath = Resolve-ServicePsqlPath -ServiceImagePath $ServiceImagePath
    if ($ServicePsqlPath) {
        Write-Log "Resolving psql.exe from service: $ServicePsqlPath"
        $Psql = $ServicePsqlPath
    }
}

Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL START"
Write-Log "======================================="
Write-Log "Project Root   : $ProjectRoot"
Write-Log "Host           : $PgHost"
Write-Log "Port           : $ExpectedPort"
Write-Log "Database       : $PgDatabase"
Write-Log "User           : $PgUser"
Write-Log "pg_ctl         : $PgCtl"
Write-Log "psql           : $Psql"
Write-Log "Data Dir       : $PgData"
Write-Log "Log File       : $PgLog"

# =====================================
# CHECK CONFIGURED CONNECTION
# =====================================

$env:PGPASSWORD = $Config["POSTGRESQL_PASSWORD"]

if (Test-Path $Psql) {
    $PreviousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    & "$Psql" --host="$PgHost" --port="$ExpectedPort" --username="$PgUser" --dbname="postgres" --command="SELECT 1;" *> $null
    $ConfiguredConnectionExitCode = $LASTEXITCODE
    $ErrorActionPreference = $PreviousErrorActionPreference
} else {
    Write-Log "psql.exe not available. Skipping configured connection check."
    $ConfiguredConnectionExitCode = 1
}

$env:PGPASSWORD = $null

if ($ConfiguredConnectionExitCode -eq 0) {
    Write-Log "Configured PostgreSQL is already reachable."
    exit 0
}

# =====================================
# CHECK SERVICE
# =====================================

$ExistingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($ExistingService) {

    if ($ExistingService.Status -eq "Running") {
        Write-Log "Windows Service already running."
        Write-Log "Reusing existing PostgreSQL instance."
        exit 0
    }

    $ServiceImagePathFromCim = Get-ServiceImagePath -Name $ServiceName
    $ServiceInWorkspace = $false
    if ($ServiceImagePathFromCim) {
        $ServiceInWorkspace = $ServiceImagePathFromCim -like "*$ProjectRoot*"
    }

    Write-Log ""
    Write-Log "======================================="
    Write-Log "PRE-START SERVICE DIAGNOSTICS"
    Write-Log "======================================="
    Write-Log "Service Name            : $ServiceName"
    Write-Log "Service Exists          : True"
    Write-Log "Service Status          : $($ExistingService.Status)"
    Write-Log "Service StartType       : $($ExistingService.StartType)"
    Write-Log "Service Binary Path     : $ServiceImagePathFromCim"
    Write-Log "Current Project Root    : $ProjectRoot"
    Write-Log "Expected Bin Directory  : $PgBin"
    Write-Log "Expected Data Directory : $PgData"
    Write-Log "ImagePath In Workspace  : $ServiceInWorkspace"
    Write-Log "======================================="

    if ($ServiceInWorkspace) {
        Write-Log "Starting existing PostgreSQL service..."

        try {
            Start-Service -Name $ServiceName
        }
        catch {
            Write-Log ""
            Write-Log "======================================="
            Write-Log "START-SERVICE FAILURE DIAGNOSTICS"
            Write-Log "======================================="
            Write-Log "Exception Message       : $($_.Exception.Message)"
            if ($_.Exception -is [System.ComponentModel.Win32Exception]) {
                Write-Log "Win32 NativeErrorCode   : $($_.Exception.NativeErrorCode)"
            }
            if ($_.Exception.GetType().FullName -eq "System.ServiceProcess.ServiceCommandException") {
                Write-Log "ServiceCommandException : True"
            }

            $SvcAfterFailure = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
            if ($SvcAfterFailure) {
                Write-Log "Service State After Failure : $($SvcAfterFailure.Status)"
            }

            Write-Log ""
            Write-Log "sc qc $ServiceName"
            Write-Log ""
            sc qc $ServiceName 2>&1 | ForEach-Object { Write-Log $_ }

            Write-Log ""
            Write-Log "sc query $ServiceName"
            Write-Log ""
            sc query $ServiceName 2>&1 | ForEach-Object { Write-Log $_ }

            Write-Log ""
            Write-Log "Get-CimInstance Win32_Service -Filter `"Name='$ServiceName'`""
            Write-Log ""
            $CimInfo = Get-CimInstance Win32_Service -Filter "Name='$ServiceName'" -ErrorAction SilentlyContinue
            if ($CimInfo) {
                $CimInfo | Format-List * | Out-String -Stream | ForEach-Object { Write-Log $_ }
            }
            else {
                Write-Log "Service not found in Win32_Service CIM class."
            }

            Write-Log ""
            Write-Log "Current PostgreSQL processes:"
            Write-Log ""
            Get-Process -Name "postgres" -ErrorAction SilentlyContinue | Format-Table Id, ProcessName, Path, StartTime | Out-String -Stream | ForEach-Object { Write-Log $_ }

            Write-Log ""
            Write-Log "Port usage for PostgreSQL port $($ExpectedPort):"
            Write-Log ""
            $PortConnections = Get-NetTCPConnection -LocalPort $ExpectedPort -State Listen -ErrorAction SilentlyContinue
            if ($PortConnections) {
                $PortConnections | Format-Table LocalAddress, LocalPort, OwningProcess, State | Out-String -Stream | ForEach-Object { Write-Log $_ }
                $PortConnections | ForEach-Object {
                    $Proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
                    if ($Proc) {
                        Write-Log "Process owning port: $($Proc.ProcessName) (PID: $($Proc.Id), Path: $($Proc.Path))"
                    }
                }
            }
            else {
                Write-Log "No process listening on port $ExpectedPort."
            }

            Write-Log "======================================="
            Write-Log "Falling back to pg_ctl start due to service start failure."
        }
    }
    else {
        Write-Log "Service is registered outside workspace. Re-registering..."

        if ($ExistingService.Status -ne "Stopped") {
            Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
            Write-Log "Stopped existing service."
        }

        & "$PgCtl" unregister -N $ServiceName
        Write-Log "Unregistered PostgreSQLAutomation service."

        $PgCtlRegisterArgs = @("register", "-N", "`"$ServiceName`"", "-S", "auto", "-D", "`"$PgData`"", "-o", "`"-p $ExpectedPort`"")
        & "$PgCtl" @PgCtlRegisterArgs
        Write-Log "Registered PostgreSQLAutomation service."

        Start-Service -Name $ServiceName
        Write-Log "Started PostgreSQLAutomation service."

        $SvcStatus = $null
        for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
            Start-Sleep -Seconds 1
            $SvcStatus = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
            if ($SvcStatus -and $SvcStatus.Status -eq "Running") {
                Write-Log "Windows Service is running."
                break
            }
            Write-Log "Waiting for service to start... $Attempt/30"
        }

        if (-not $SvcStatus -or $SvcStatus.Status -ne "Running") {
            throw "PostgreSQLAutomation service failed to reach Running state within 30 seconds."
        }

        if (Test-Path $Psql) {
            $env:PGPASSWORD = $Config["POSTGRESQL_PASSWORD"]
            $PreviousErrorActionPreference = $ErrorActionPreference
            $ErrorActionPreference = "Continue"
            & "$Psql" --host="$PgHost" --port="$ExpectedPort" --username="$PgUser" --dbname="postgres" --command="SELECT 1;" *> $null
            $PsqlExitCode = $LASTEXITCODE
            $ErrorActionPreference = $PreviousErrorActionPreference
            $env:PGPASSWORD = $null

            if ($PsqlExitCode -eq 0) {
                Write-Log "PostgreSQL is reachable via Windows Service."
                exit 0
            }

            throw "PostgreSQLAutomation service started but PostgreSQL is not reachable."
        }

        Write-Log "Windows Service started successfully."
        exit 0
    }
}

# =====================================
# PORT CONFLICT CHECK
# =====================================

Write-Log "Checking configured port $ExpectedPort..."

$PortConnection = Get-NetTCPConnection `
    -LocalPort $ExpectedPort `
    -State Listen `
    -ErrorAction SilentlyContinue |
    Select-Object -First 1

if ($PortConnection) {

    $OwnerProcessId = $PortConnection.OwningProcess
    $OwnerProcess = Get-Process -Id $OwnerProcessId -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "======================================="
    Write-Host "PORT CONFLICT"
    Write-Host "======================================="
    Write-Host "Port       : $ExpectedPort"
    Write-Host "Process ID : $OwnerProcessId"

    if ($OwnerProcess) {
        Write-Host "Process    : $($OwnerProcess.ProcessName)"
    }

    if ($OwnerProcess -and $OwnerProcess.ProcessName -eq "postgres") {
        Write-Host ""
        Write-Host "Detected PostgreSQL on configured port. Validating connection..."

        if (Test-Path $Psql) {
            $env:PGPASSWORD = $Config["POSTGRESQL_PASSWORD"]
            $PreviousErrorActionPreference = $ErrorActionPreference
            $ErrorActionPreference = "Continue"
            & "$Psql" --host="$PgHost" --port="$ExpectedPort" --username="$PgUser" --dbname="postgres" --command="SELECT 1;" *> $null
            $PsqlExitCode = $LASTEXITCODE
            $ErrorActionPreference = $PreviousErrorActionPreference
            $env:PGPASSWORD = $null

            if ($PsqlExitCode -eq 0) {
                Write-Host ""
                Write-Host "Configured PostgreSQL is already reachable."
                exit 0
            }
        }

        throw "Detected foreign PostgreSQL on port $ExpectedPort. Cannot start a new instance."
    }

    throw "Port $ExpectedPort is already occupied by $($OwnerProcess.ProcessName)."
}

Write-Log "Port $ExpectedPort is available."

# =====================================
# VALIDATE WORKSPACE BINARIES
# =====================================

if (!(Test-Path $PgCtl)) {
    throw "pg_ctl.exe not found: $PgCtl"
}

if (!(Test-Path $Psql)) {
    throw "psql.exe not found: $Psql"
}

if (!(Test-Path (Join-Path $PgData "PG_VERSION"))) {
    throw "PostgreSQL data directory is not initialized: $PgData"
}

# =====================================
# START POSTGRESQL
# =====================================

$PgCtlOutput = Join-Path $LogDirectory "pg_ctl_start_output.log"
$PgCtlError = Join-Path $LogDirectory "pg_ctl_start_error.log"
if (Test-Path $PgCtlOutput) { Remove-Item $PgCtlOutput -Force }
if (Test-Path $PgCtlError) { Remove-Item $PgCtlError -Force }

Write-Log "Starting PostgreSQL..."
$PgCtlArguments = @("start", "-D", "`"$PgData`"", "-l", "`"$PgLog`"", "-o", "`"-p $ExpectedPort`"", "-w", "-t", "60")
$PreviousErrorActionPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
# & "$PgCtl" @PgCtlArguments > $PgCtlOutput 2> $PgCtlError
# $PgCtlExitCode = $LASTEXITCODE
Write-Log "Calling pg_ctl..."

& "$PgCtl" @PgCtlArguments > $PgCtlOutput 2> $PgCtlError

Write-Log "pg_ctl returned. ExitCode = $LASTEXITCODE"

$PgCtlExitCode = $LASTEXITCODE
$ErrorActionPreference = $PreviousErrorActionPreference

if ($PgCtlExitCode -ne 0) {
    throw "pg_ctl start failed with exit code $PgCtlExitCode."
}

$PostgreSQLReady = $false
for ($Attempt = 1; $Attempt -le 30; $Attempt++) {
    Start-Sleep -Seconds 1

    & "$PgCtl" status -D "$PgData" *> $null
    $StatusExitCode = $LASTEXITCODE

    if ($StatusExitCode -eq 0) {
        try {
            $TcpClient = New-Object System.Net.Sockets.TcpClient
            $TcpClient.Connect($PgHost, $ExpectedPort)
            $TcpClient.Close()
            $PostgreSQLReady = $true
            Write-Log "PostgreSQL process is running."
            Write-Log "PostgreSQL port is reachable."
            break
        }
        catch {
            Write-Log "PostgreSQL process started. Waiting for port... $Attempt/30"
        }
    }
    else {
        Write-Log "Waiting for PostgreSQL startup... $Attempt/30"
    }
}

if (!$PostgreSQLReady) {
    Write-Host ""
    Write-Host "======================================="
    Write-Host "POSTGRESQL FAILED TO START"
    Write-Host "======================================="

    if (Test-Path $PgCtlOutput) {
        Write-Host ""
        Write-Host "PG_CTL OUTPUT:"
        Write-Host ""
        Get-Content $PgCtlOutput
    }

    if (Test-Path $PgCtlError) {
        Write-Host ""
        Write-Host "PG_CTL ERROR:"
        Write-Host ""
        Get-Content $PgCtlError
    }

    if (Test-Path $PgLog) {
        Write-Host ""
        Write-Host "LAST POSTGRESQL LOG ENTRIES:"
        Write-Host ""
        Get-Content $PgLog -Tail 50
    }

    throw "PostgreSQL failed to become ready within 30 seconds."
}

Write-Log "PostgreSQL startup completed successfully."
Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL START COMPLETED"
Write-Log "======================================="
Write-Log "Host      : $PgHost"
Write-Log "Port      : $ExpectedPort"
Write-Log "Database  : $PgDatabase"
Write-Log "User      : $PgUser"
Write-Log "Data Dir  : $PgData"
Write-Log "Log File  : $PgLog"

exit 0
