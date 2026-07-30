$ErrorActionPreference = "Stop"

# Project root
$ProjectRoot = Split-Path $PSScriptRoot -Parent
$ProjectRoot = Split-Path $ProjectRoot -Parent

# Read config
$ConfigFile = Join-Path $ProjectRoot "config\windows\mysql.conf"

$Config = @{}

Get-Content $ConfigFile | ForEach-Object {

    if ($_ -match "=") {

        $Key, $Value = $_ -split "=", 2

        $Config[$Key.Trim()] = $Value.Trim()
    }
}

$Port = $Config["MYSQL_PORT"]

$Connection = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue

if ($null -eq $Connection) {

    Write-Host ""
    Write-Host "====================================="
    Write-Host "MySQL Already Stopped"
    Write-Host "Port : $Port"
    Write-Host "====================================="

    exit 0
}

$ProcessId = $Connection.OwningProcess

Stop-Process -Id $ProcessId -Force

Write-Host ""
Write-Host "====================================="
Write-Host "MySQL Stopped Successfully"
Write-Host "Port : $Port"
Write-Host "PID  : $ProcessId"
Write-Host "====================================="