$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$configFile = "$ROOT\config\windows\mysql.conf"
$mysqldPath = "$ROOT\databases\mysql\server\bin\mysqld.exe"

Write-Host ""
Write-Host "====================================="
Write-Host "STOPPING MYSQL"
Write-Host "====================================="
Write-Host ""

if (!(Test-Path $configFile)) {
    throw "Config file not found: $configFile"
}

$port = (
    Get-Content $configFile |
    Where-Object { $_ -match "^MYSQL_PORT=" } |
    ForEach-Object { ($_ -split "=", 2)[1].Trim() }
)

if ([string]::IsNullOrWhiteSpace($port)) {
    throw "MYSQL_PORT not found in config file"
}

Write-Host "Port       : $port"
Write-Host "MySQL Path : $mysqldPath"
Write-Host ""

$mysqlProcesses = Get-CimInstance Win32_Process -Filter "Name='mysqld.exe'" |
    Where-Object {
        $_.ExecutablePath -and
        $_.ExecutablePath -ieq $mysqldPath
    }

if (!$mysqlProcesses) {
    Write-Host "Automation-managed MySQL process is already stopped."
}
else {
    foreach ($process in $mysqlProcesses) {
        Write-Host "Stopping MySQL process (PID: $($process.ProcessId))"

        Stop-Process -Id $process.ProcessId -Force
    }

    Start-Sleep -Seconds 3
}

Write-Host ""
Write-Host "Validating MySQL process status..."

$remainingProcesses = Get-CimInstance Win32_Process -Filter "Name='mysqld.exe'" |
    Where-Object {
        $_.ExecutablePath -and
        $_.ExecutablePath -ieq $mysqldPath
    }

if ($remainingProcesses) {
    throw "Automation-managed MySQL process is still running"
}

Write-Host ""
Write-Host "====================================="
Write-Host "MYSQL STOPPED SUCCESSFULLY"
Write-Host "====================================="
Write-Host ""

exit 0