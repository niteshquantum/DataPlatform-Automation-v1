
$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

$configFile = "$ROOT\config\windows\mysql.conf"

if (!(Test-Path $configFile)) {
    throw "Config file not found: $configFile"
}

$port = (
    Get-Content $configFile |
    Where-Object { $_ -match "^MYSQL_PORT=" } |
    ForEach-Object { ($_ -split "=")[1].Trim() }
)

$baseDir = "$ROOT\databases\mysql\server"
$dataDir = "$ROOT\databases\mysql\data"
$mysqld  = "$baseDir\bin\mysqld.exe"
$mysqladmin = "$baseDir\bin\mysqladmin.exe"

Write-Host ""
Write-Host "====================================="
Write-Host "STARTING MYSQL"
Write-Host "====================================="
Write-Host "BaseDir : $baseDir"
Write-Host "DataDir : $dataDir"
Write-Host "Port    : $port"
Write-Host ""

# =====================================
# VALIDATE FILES
# =====================================
if (!(Test-Path $mysqld)) {

    $portCheck = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1

    if ($portCheck) {

        Write-Host ""
        Write-Host "MySQL is already running on port $port."
        Write-Host "Skipping project-local start."
        Write-Host ""
        exit 0
    }

    throw "mysqld.exe not found: $mysqld"
}

if (!(Test-Path $mysqladmin)) {

    throw "mysqladmin.exe not found: $mysqladmin"
}
if (!(Test-Path $dataDir)) {
    throw "Data directory not found: $dataDir"
}

# =====================================
# STOP OLD MYSQL PROCESS
# =====================================

Get-Process mysqld -ErrorAction SilentlyContinue |
ForEach-Object {
    $processPath = $null

    try {
        $processPath = $_.Path
    }
    catch {
        Write-Host "Skipping mysqld process with unreadable path (PID: $($_.Id))"
        continue
    }

    if ($processPath -ne $mysqld) {
        Write-Host "Skipping non-project mysqld process (PID: $($_.Id))"
        continue
    }

    Write-Host "Stopping existing project mysqld process (PID: $($_.Id))"

    try {
        Stop-Process -Id $_.Id -Force -ErrorAction Stop
    }
    catch {
        Write-Host "WARNING: Could not stop project mysqld process (PID: $($_.Id)): $($_.Exception.Message)"
    }
}

Start-Sleep -Seconds 3

# =====================================
# START MYSQL
# =====================================
$env:JENKINS_NODE_COOKIE = "MySQLAutomationProcess"
Start-Process `
    -FilePath $mysqld `
    -ArgumentList @(
        "--port=$port",
        "--basedir=$baseDir",
        "--datadir=$dataDir"
    ) `
    -WindowStyle Hidden

# =====================================
# WAIT FOR MYSQL TO ACCEPT CONNECTIONS
# =====================================

$started = $false

for ($i = 1; $i -le 60; $i++) {

    try {

        & $mysqladmin `
            --host=127.0.0.1 `
            --port=$port `
            -u root `
            ping 2>$null | Out-Null

        if ($LASTEXITCODE -eq 0) {
            $started = $true
            break
        }

    }
    catch {
    }

    Start-Sleep -Seconds 1
}

if (-not $started) {

    Write-Host ""
    Write-Host "MySQL error log:"
    Write-Host "-------------------------------------"

    Get-ChildItem $dataDir -Filter "*.err" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1 |
    ForEach-Object {
        Get-Content $_.FullName -Tail 30
    }

    throw "MySQL failed to start on port $port"
}

Write-Host ""
Write-Host "====================================="
Write-Host "MYSQL START SUCCESSFUL"
Write-Host "Port : $port"
Write-Host "====================================="
Write-Host ""

