$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

# =====================================================
# PROJECT ROOT AND PATHS
# =====================================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

$MongoHome = Join-Path $PROJECT_ROOT "databases\mongodb"
$MongodExe = Join-Path $MongoHome "server\bin\mongod.exe"
$DataPath  = Join-Path $MongoHome "data"
$LogDir    = Join-Path $MongoHome "logs"
$LogPath   = Join-Path $LogDir "mongodb.log"

$ServiceName        = "MongoDBAutomation"
$ServiceDisplayName = "MongoDB Automation Service"

# =====================================================
# READ CONFIGURATION
# =====================================================

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
$MongoPort = [int]$Config["MONGODB_PORT"]

# =====================================================
# VALIDATE CONFIGURATION
# =====================================================

if ([string]::IsNullOrWhiteSpace($MongoHost)) {
    throw "MONGODB_HOST not found in mongodb.conf"
}

if ($MongoPort -le 0) {
    throw "Invalid MONGODB_PORT in mongodb.conf"
}

if (!(Test-Path $MongodExe)) {
    throw "mongod.exe not found: $MongodExe"
}

# =====================================================
# CREATE REQUIRED DIRECTORIES
# =====================================================

if (!(Test-Path $DataPath)) {
    New-Item `
        -ItemType Directory `
        -Path $DataPath `
        -Force | Out-Null
}

if (!(Test-Path $LogDir)) {
    New-Item `
        -ItemType Directory `
        -Path $LogDir `
        -Force | Out-Null
}

# =====================================================
# START REPORT
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "CONFIGURING MONGODB WINDOWS SERVICE"
Write-Log "======================================="

Write-Log "Project Root : $PROJECT_ROOT"
Write-Log "MongoDB      : $MongodExe"
Write-Log "Data Path    : $DataPath"
Write-Log "Log Path     : $LogPath"
Write-Log "Host         : $MongoHost"
Write-Log "Port         : $MongoPort"
Write-Log "Service      : $ServiceName"

# =====================================================
# CHECK ADMINISTRATOR PRIVILEGES
# DEFENSE-IN-DEPTH VALIDATION
# =====================================================

$Identity = [Security.Principal.WindowsIdentity]::GetCurrent()

$Principal = New-Object `
    Security.Principal.WindowsPrincipal($Identity)

$IsAdmin = $Principal.IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (!$IsAdmin) {
    throw "Administrator privileges are required to configure MongoDB Windows Service."
}

Write-Log "Administrator privileges verified."

# =====================================================
# CHECK EXISTING SERVICE
# =====================================================

$ExistingService = Get-Service `
    -Name $ServiceName `
    -ErrorAction SilentlyContinue

if ($ExistingService) {

    Write-Log "Existing MongoDB service found."

    if ($ExistingService.Status -eq "Running") {

        Write-Log "Stopping existing MongoDB service..."

        Stop-Service `
            -Name $ServiceName `
            -Force `
            -ErrorAction Stop

        $ExistingService.WaitForStatus(
            "Stopped",
            (New-TimeSpan -Seconds 60)
        )

        Write-Log "Existing MongoDB service stopped."
    }

    # =================================================
    # REMOVE EXISTING SERVICE
    # =================================================

    Write-Log "Removing existing MongoDB service..."

    & sc.exe delete $ServiceName | Out-Null

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to remove existing MongoDB service."
    }

    # Wait until Windows Service Manager removes it

    for ($Attempt = 1; $Attempt -le 30; $Attempt++) {

        $ServiceCheck = Get-Service `
            -Name $ServiceName `
            -ErrorAction SilentlyContinue

        if (!$ServiceCheck) {
            break
        }

        Write-Log "Waiting for old service removal... $Attempt/30"

        Start-Sleep -Seconds 1
    }

    $ServiceCheck = Get-Service `
        -Name $ServiceName `
        -ErrorAction SilentlyContinue

    if ($ServiceCheck) {
        throw "Existing MongoDB service could not be removed."
    }

    Write-Log "Existing MongoDB service removed."
}

# =====================================================
# CHECK CONFIGURED PORT
# =====================================================

Write-Log "Checking configured port $MongoPort..."

$PortConnection = Get-NetTCPConnection `
    -LocalPort $MongoPort `
    -State Listen `
    -ErrorAction SilentlyContinue |
    Select-Object -First 1

if ($PortConnection) {

    $OwnerProcessId = $PortConnection.OwningProcess

    $OwnerProcess = Get-Process `
        -Id $OwnerProcessId `
        -ErrorAction SilentlyContinue

    Write-Host ""
    Write-Host "======================================="
    Write-Host "PORT CONFLICT"
    Write-Host "======================================="

    Write-Host "Port       : $MongoPort"
    Write-Host "Process ID : $OwnerProcessId"

    if ($OwnerProcess) {
        Write-Host "Process    : $($OwnerProcess.ProcessName)"
    }

    throw "Port $MongoPort is already occupied."
}

Write-Log "Port $MongoPort is available."

# =====================================================
# INSTALL MONGODB WINDOWS SERVICE
# =====================================================

Write-Log "Installing MongoDB Windows Service..."

& "$MongodExe" `
    --dbpath "$DataPath" `
    --logpath "$LogPath" `
    --logappend `
    --bind_ip "$MongoHost" `
    --port "$MongoPort" `
    --serviceName "$ServiceName" `
    --serviceDisplayName "$ServiceDisplayName" `
    --install

if ($LASTEXITCODE -ne 0) {
    throw "MongoDB Windows Service installation failed."
}

# =====================================================
# VERIFY SERVICE REGISTRATION
# =====================================================

$Service = Get-Service `
    -Name $ServiceName `
    -ErrorAction SilentlyContinue

if (!$Service) {
    throw "MongoDB service installation completed but service was not found."
}

Write-Log "MongoDB Windows Service installed successfully."

# =====================================================
# CONFIGURE AUTOMATIC START
# =====================================================

Write-Log "Configuring automatic service startup..."

& sc.exe config $ServiceName start= auto | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Failed to configure MongoDB service automatic startup."
}

Write-Log "Automatic service startup configured."

# =====================================================
# START MONGODB SERVICE
# =====================================================

Write-Log "Starting MongoDB Windows Service..."

Start-Service `
    -Name $ServiceName `
    -ErrorAction Stop

# =====================================================
# WAIT FOR SERVICE
# =====================================================

$ServiceStarted = $false

for ($Attempt = 1; $Attempt -le 30; $Attempt++) {

    $Service = Get-Service `
        -Name $ServiceName `
        -ErrorAction SilentlyContinue

    if (
        $Service -and
        $Service.Status -eq "Running"
    ) {
        $ServiceStarted = $true
        break
    }

    Write-Log "Waiting for MongoDB service... $Attempt/30"

    Start-Sleep -Seconds 1
}

if (!$ServiceStarted) {

    if (Test-Path $LogPath) {

        Write-Host ""
        Write-Host "LAST MONGODB LOG ENTRIES:"
        Write-Host ""

        Get-Content $LogPath -Tail 50
    }

    throw "MongoDB Windows Service failed to start."
}

Write-Log "MongoDB Windows Service is running."

# =====================================================
# WAIT FOR PORT
# =====================================================

Write-Log "Checking MongoDB port..."

$PortReady = $false

for ($Attempt = 1; $Attempt -le 30; $Attempt++) {

    try {

        $TcpClient = New-Object System.Net.Sockets.TcpClient

        $TcpClient.Connect(
            $MongoHost,
            $MongoPort
        )

        $TcpClient.Close()

        $PortReady = $true
        break
    }
    catch {

        Write-Log "Waiting for MongoDB port... $Attempt/30"

        Start-Sleep -Seconds 1
    }
}

if (!$PortReady) {

    if (Test-Path $LogPath) {

        Write-Host ""
        Write-Host "LAST MONGODB LOG ENTRIES:"
        Write-Host ""

        Get-Content $LogPath -Tail 50
    }

    throw "MongoDB service started but port $MongoPort is not reachable."
}

Write-Log "MongoDB port is reachable."

# =====================================================
# FINAL SERVICE VALIDATION
# =====================================================

$Service = Get-Service `
    -Name $ServiceName `
    -ErrorAction Stop

if ($Service.Status -ne "Running") {
    throw "MongoDB Windows Service is not running."
}

# =====================================================
# SUCCESS
# =====================================================

Write-Log ""
Write-Log "======================================="
Write-Log "MONGODB WINDOWS SERVICE CONFIGURED"
Write-Log "======================================="

Write-Log "Service : $ServiceName"
Write-Log "Status  : $($Service.Status)"
Write-Log "Startup : Automatic"
Write-Log "Host    : $MongoHost"
Write-Log "Port    : $MongoPort"
Write-Log "Data    : $DataPath"
Write-Log "Log     : $LogPath"

exit 0
