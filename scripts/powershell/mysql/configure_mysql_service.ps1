$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "CONFIGURING MYSQL WINDOWS SERVICE"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

$ConfigFile = "$ROOT\config\windows\mysql.conf"
$BaseDir    = "$ROOT\databases\mysql\server"
$DataDir    = "$ROOT\databases\mysql\data"
$Mysqld     = "$BaseDir\bin\mysqld.exe"
$MyIni      = "$ROOT\databases\mysql\my.ini"

$ServiceName = "MySQLAutomation"

# =====================================
# VALIDATE CONFIG FILE
# =====================================

if (!(Test-Path $ConfigFile)) {
    throw "Config file not found: $ConfigFile"
}

# =====================================
# READ CONFIG
# =====================================

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

$MySQLHost = $Config["MYSQL_HOST"]
$MySQLPort = $Config["MYSQL_PORT"]

if (-not $MySQLHost) {
    throw "MYSQL_HOST not found in mysql.conf"
}

if (-not $MySQLPort) {
    throw "MYSQL_PORT not found in mysql.conf"
}

# =====================================
# VALIDATE MYSQL
# =====================================

if (!(Test-Path $Mysqld)) {
    throw "mysqld.exe not found: $Mysqld"
}

if (!(Test-Path $DataDir)) {
    throw "MySQL data directory not found: $DataDir"
}

Write-Host "Project Root : $ROOT"
Write-Host "MySQL        : $Mysqld"
Write-Host "BaseDir      : $BaseDir"
Write-Host "DataDir      : $DataDir"
Write-Host "Host         : $MySQLHost"
Write-Host "Port         : $MySQLPort"
Write-Host "Service      : $ServiceName"
Write-Host ""

# =====================================
# CREATE MY.INI
# =====================================

Write-Host "Creating MySQL configuration file..."

$BaseDirConfig = $BaseDir.Replace("\", "/")
$DataDirConfig = $DataDir.Replace("\", "/")

$MyIniContent = @"
[mysqld]
basedir=$BaseDirConfig
datadir=$DataDirConfig
port=$MySQLPort
bind-address=$MySQLHost
"@

Set-Content `
    -Path $MyIni `
    -Value $MyIniContent `
    -Encoding ASCII

if (!(Test-Path $MyIni)) {
    throw "Failed to create my.ini"
}

Write-Host "Configuration : $MyIni"

# =====================================
# CHECK PROJECT MYSQL INSTANCE
# =====================================

Write-Host ""
Write-Host "Checking MySQL instance on configured port $MySQLPort..."

$PortConnection = Get-NetTCPConnection `
    -LocalPort $MySQLPort `
    -State Listen `
    -ErrorAction SilentlyContinue |
    Select-Object -First 1

if ($PortConnection) {

    $MySQLProcessId = $PortConnection.OwningProcess

    Write-Host "Process found on configured port."
    Write-Host "Port       : $MySQLPort"
    Write-Host "Process ID : $MySQLProcessId"

    $MySQLProcess = Get-Process `
        -Id $MySQLProcessId `
        -ErrorAction SilentlyContinue

    if (
        $MySQLProcess -and
        $MySQLProcess.ProcessName -eq "mysqld"
    ) {

        Write-Host "Stopping MySQL process PID: $MySQLProcessId"

        Stop-Process `
            -Id $MySQLProcessId `
            -Force

        Start-Sleep -Seconds 3
    }
    else {

        throw "Port $MySQLPort is occupied by a non-MySQL process."
    }
}
else {

    Write-Host "No standalone MySQL instance found on port $MySQLPort."
}

# =====================================
# CHECK EXISTING MYSQL SERVICE
# =====================================

Write-Host ""
Write-Host "Checking existing MySQL Windows Service..."

$ExistingService = Get-Service `
    -Name $ServiceName `
    -ErrorAction SilentlyContinue

if ($ExistingService) {

    Write-Host "Existing MySQL service detected."

    # =====================================
    # STOP EXISTING SERVICE
    # =====================================

    if ($ExistingService.Status -ne "Stopped") {

        Write-Host "Stopping existing MySQL service..."

        Stop-Service `
            -Name $ServiceName `
            -Force `
            -ErrorAction SilentlyContinue

        # WAIT FOR SERVICE TO STOP

        $ServiceStopped = $false

        for ($i = 1; $i -le 30; $i++) {

            $ServiceCheck = Get-Service `
                -Name $ServiceName `
                -ErrorAction SilentlyContinue

            if (
                $ServiceCheck -and
                $ServiceCheck.Status -eq "Stopped"
            ) {

                $ServiceStopped = $true
                break
            }

            Write-Host "Waiting for MySQL service to stop... $i/30"

            Start-Sleep -Seconds 1
        }

        if (-not $ServiceStopped) {
            throw "Existing MySQL service failed to stop"
        }

        Write-Host "Existing MySQL service stopped successfully."
    }

    # =====================================
    # REMOVE EXISTING SERVICE
    # =====================================

    Write-Host "Removing existing MySQL service..."

    & sc.exe delete $ServiceName

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to remove existing MySQL service"
    }

    # =====================================
    # WAIT FOR SERVICE REMOVAL
    # =====================================

    $ServiceRemoved = $false

    for ($i = 1; $i -le 30; $i++) {

        $ServiceCheck = Get-Service `
            -Name $ServiceName `
            -ErrorAction SilentlyContinue

        if (-not $ServiceCheck) {

            $ServiceRemoved = $true
            break
        }

        Write-Host "Waiting for old service removal... $i/30"

        Start-Sleep -Seconds 1
    }

    if (-not $ServiceRemoved) {
        throw "Existing MySQL service could not be completely removed"
    }

    Write-Host "Existing MySQL service removed successfully."
}
else {

    Write-Host "No existing MySQL service found."
}

# =====================================
# INSTALL MYSQL SERVICE
# =====================================

Write-Host ""
Write-Host "Installing MySQL Windows Service..."

$InstallOutput = & $Mysqld `
    --install $ServiceName `
    "--defaults-file=$MyIni" 2>&1

$InstallExitCode = $LASTEXITCODE

$InstallOutput | ForEach-Object {
    Write-Host $_
}

if ($InstallExitCode -ne 0) {

    Write-Host ""
    Write-Host "====================================="
    Write-Host "MYSQL SERVICE INSTALLATION FAILED"
    Write-Host "====================================="
    Write-Host "Exit Code : $InstallExitCode"
    Write-Host "Service   : $ServiceName"
    Write-Host "Config    : $MyIni"
    Write-Host ""

    throw "MySQL Windows Service installation failed"
}

Write-Host "MySQL Windows Service installed successfully."


# =====================================
# VALIDATE SERVICE EXISTS
# =====================================

$InstalledService = Get-Service `
    -Name $ServiceName `
    -ErrorAction SilentlyContinue

if (-not $InstalledService) {
    throw "MySQL service was not created"
}

Write-Host "MySQL Windows Service validation successful."

# =====================================
# CONFIGURE AUTO START
# =====================================

Write-Host ""
Write-Host "Configuring MySQL service automatic startup..."

& sc.exe config $ServiceName start= auto

if ($LASTEXITCODE -ne 0) {
    throw "Failed to configure automatic startup"
}

Write-Host "Automatic startup configured successfully."

# =====================================
# START SERVICE
# =====================================

Write-Host ""
Write-Host "Starting MySQL Windows Service..."

Start-Service -Name $ServiceName

# =====================================
# WAIT FOR SERVICE
# =====================================

$ServiceStarted = $false

for ($i = 1; $i -le 60; $i++) {

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

    Write-Host "Waiting for MySQL service startup... $i/60"

    Start-Sleep -Seconds 1
}

if (-not $ServiceStarted) {
    throw "MySQL Windows Service failed to start"
}

Write-Host "MySQL Windows Service started successfully."

# =====================================
# WAIT FOR MYSQL PORT
# =====================================

Write-Host ""
Write-Host "Waiting for MySQL port $MySQLPort..."

$PortStarted = $false

for ($i = 1; $i -le 60; $i++) {

    $PortCheck = Get-NetTCPConnection `
        -LocalPort $MySQLPort `
        -State Listen `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if ($PortCheck) {

        $PortStarted = $true
        break
    }

    Write-Host "Waiting for MySQL port... $i/60"

    Start-Sleep -Seconds 1
}

if (-not $PortStarted) {
    throw "MySQL is not listening on port $MySQLPort"
}

# =====================================
# SUCCESS
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "MYSQL WINDOWS SERVICE CONFIGURED"
Write-Host "====================================="
Write-Host ""
Write-Host "Service : $ServiceName"
Write-Host "Status  : Running"
Write-Host "Startup : Automatic"
Write-Host "Host    : $MySQLHost"
Write-Host "Port    : $MySQLPort"
Write-Host ""

exit 0
