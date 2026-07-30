
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "CONFIGURING POSTGRESQL WINDOWS SERVICE"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

$PgBin  = "$PROJECT_ROOT\databases\postgresql\bin"
$PgData = "$PROJECT_ROOT\databases\postgresql\data"
$PgLogDir = "$PROJECT_ROOT\outputs\logs"
$PgLog  = "$PgLogDir\postgresql_service.log"

$PgCtl = "$PgBin\pg_ctl.exe"
$ResolvedPgCtlFromService = $false

$ServiceName = "PostgreSQLAutomation"

# =====================================
# READ CONFIG
# =====================================

$ConfigFile = "$PROJECT_ROOT\config\windows\postgresql.conf"

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

$PgHost     = $Config["POSTGRESQL_HOST"]
$PgPort     = $Config["POSTGRESQL_PORT"]
$PgDatabase = $Config["POSTGRESQL_DB"]
$PgUser     = $Config["POSTGRESQL_USER"]

if (-not $PgHost) {
    throw "POSTGRESQL_HOST not found in postgresql.conf"
}

if (-not $PgPort) {
    throw "POSTGRESQL_PORT not found in postgresql.conf"
}

if (-not $PgUser) {
    throw "POSTGRESQL_USER not found in postgresql.conf"
}

Write-Host "Project Root : $PROJECT_ROOT"
Write-Host "PostgreSQL   : $PgCtl"
Write-Host "Data Path    : $PgData"
Write-Host "Log Path     : $PgLog"
Write-Host "Host         : $PgHost"
Write-Host "Port         : $PgPort"
Write-Host "Database     : $PgDatabase"
Write-Host "User         : $PgUser"
Write-Host "Service      : $ServiceName"
Write-Host ""

# =====================================
# VALIDATE FILES
# =====================================

if (!(Test-Path $PgCtl)) {

    Write-Host ""
    Write-Host "Resolving pg_ctl.exe from existing PostgreSQL service..."

    $ServiceConfiguration = Get-CimInstance `
        Win32_Service `
        -Filter "Name='$ServiceName'" `
        -ErrorAction SilentlyContinue

    if ($ServiceConfiguration -and $ServiceConfiguration.PathName) {

        $PgCtlMatch = [regex]::Match(
            $ServiceConfiguration.PathName.Trim(),
            '"?(?<path>[A-Za-z]:\\[^"\r\n]*?\\pg_ctl\.exe)"?',
            [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
        )

        if ($PgCtlMatch.Success) {

            $ServicePgCtl = $PgCtlMatch.Groups['path'].Value.Trim('"')

            if (Test-Path -LiteralPath $ServicePgCtl -PathType Leaf) {
                Write-Host "Resolved pg_ctl.exe from service: $ServicePgCtl"
                $PgCtl = $ServicePgCtl
                $ResolvedPgCtlFromService = $true
            }
        }
    }

    if (!(Test-Path $PgCtl)) {
        throw "pg_ctl.exe not found in workspace: $PgBin. Unable to resolve it from the PostgreSQLAutomation service."
    }
}

if ($ResolvedPgCtlFromService) {

    $PgDataMatch = [regex]::Match(
        $ServiceConfiguration.PathName,
        '(?:^|\s)-D\s+(?:"(?<quotedPath>[^"]+)"|(?<unquotedPath>\S+))',
        [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
    )

    if (-not $PgDataMatch.Success) {
        throw "Unable to resolve the PostgreSQL data directory (-D) from the PostgreSQLAutomation service."
    }

    $PgData = if ($PgDataMatch.Groups['quotedPath'].Success) {
        $PgDataMatch.Groups['quotedPath'].Value
    }
    else {
        $PgDataMatch.Groups['unquotedPath'].Value
    }

    Write-Host "Resolved PostgreSQL data directory from service: $PgData"
}

if (!(Test-Path "$PgData\PG_VERSION")) {
    throw "PostgreSQL data directory is not initialized: $PgData"
}

if (!(Test-Path $PgLogDir)) {
    New-Item `
        -ItemType Directory `
        -Path $PgLogDir `
        -Force | Out-Null
}

# =====================================
# CHECK EXISTING SERVICE
# =====================================

$ExistingService = Get-Service `
    -Name $ServiceName `
    -ErrorAction SilentlyContinue

if ($ExistingService) {

    Write-Host "Existing PostgreSQL service found."

    if ($ExistingService.Status -eq "Running") {

        Write-Host "Stopping existing PostgreSQL service..."

        Stop-Service `
            -Name $ServiceName `
            -Force

        Start-Sleep -Seconds 3
    }
}

# =====================================
# STOP CURRENT PROJECT INSTANCE
# =====================================

Write-Host "Checking current project PostgreSQL instance..."

& $PgCtl status -D $PgData *> $null

if ($LASTEXITCODE -eq 0) {

    Write-Host "Stopping standalone PostgreSQL instance..."

    & $PgCtl stop -D $PgData -m fast -w

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to stop standalone PostgreSQL instance"
    }

    Start-Sleep -Seconds 3
}
else {
    Write-Host "Standalone PostgreSQL instance is not running."
}

# =====================================
# REMOVE OLD SERVICE
# =====================================

if ($ExistingService) {

    Write-Host "Removing existing PostgreSQL service..."

    & $PgCtl unregister -N $ServiceName

    Start-Sleep -Seconds 3
}

# =====================================
# REGISTER WINDOWS SERVICE
# =====================================

Write-Host ""
Write-Host "Registering PostgreSQL Windows Service..."

& $PgCtl register `
    -N $ServiceName `
    -D $PgData `
    -S auto `
    -o "-p $PgPort"

if ($LASTEXITCODE -ne 0) {
    throw "PostgreSQL service registration failed"
}

# =====================================
# START WINDOWS SERVICE
# =====================================

Write-Host "Starting PostgreSQL Windows Service..."

Start-Service -Name $ServiceName

# =====================================
# WAIT FOR SERVICE
# =====================================

$ServiceStarted = $false

for ($i = 1; $i -le 30; $i++) {

    $Service = Get-Service `
        -Name $ServiceName `
        -ErrorAction SilentlyContinue

    if ($Service -and $Service.Status -eq "Running") {

        $ServiceStarted = $true
        break
    }

    Start-Sleep -Seconds 1
}

if (-not $ServiceStarted) {
    throw "PostgreSQL Windows Service failed to start"
}

# =====================================
# WAIT FOR PORT
# =====================================

$PortStarted = $false

for ($i = 1; $i -le 30; $i++) {

    $PortConnection = Get-NetTCPConnection `
        -LocalPort $PgPort `
        -State Listen `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if ($PortConnection) {

        $PortStarted = $true
        break
    }

    Start-Sleep -Seconds 1
}

if (-not $PortStarted) {
    throw "PostgreSQL is not listening on port $PgPort"
}

Write-Host ""
Write-Host "====================================="
Write-Host "POSTGRESQL WINDOWS SERVICE CONFIGURED"
Write-Host "====================================="
Write-Host ""
Write-Host "Service : $ServiceName"
Write-Host "Status  : Running"
Write-Host "Startup : Automatic"
Write-Host "Host    : $PgHost"
Write-Host "Port    : $PgPort"
Write-Host ""

exit 0
