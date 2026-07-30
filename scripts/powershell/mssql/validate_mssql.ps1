$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "VALIDATING MSSQL SERVER"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

# =====================================
# LOAD CONFIG
# =====================================

. "$PROJECT_ROOT\scripts\powershell\common\load_config.ps1"

$Config = Load-Config "$PROJECT_ROOT\config\windows\mssql.conf"

$Server   = $Config["MSSQL_HOST"]
$Port     = $Config["MSSQL_PORT"]
$Database = $Config["MSSQL_DB"]
$User     = $Config["MSSQL_USER"]
$Password = $Config["MSSQL_PASSWORD"]
$Instance = $Config["MSSQL_INSTANCE"]

# =====================================
# SERVICE NAME
# =====================================

if ($Instance -eq "MSSQLSERVER") {
    $ServiceName = "MSSQLSERVER"
}
else {
    $ServiceName = "MSSQL`$$Instance"
}

# =====================================
# VALIDATE SERVICE
# =====================================

$Service = Get-Service `
    -Name $ServiceName `
    -ErrorAction SilentlyContinue

if (!$Service) {
    throw "SQL Server service not found."
}

if ($Service.Status -ne "Running") {
    throw "SQL Server service is not running."
}

Write-Host "[OK] SQL Server service is running."

# =====================================
# VALIDATE PORT
# =====================================

try {
    $client = [System.Net.Sockets.TcpClient]::new()
    $async = $client.BeginConnect($Server, [int]$Port, $null, $null)

    if (-not $async.AsyncWaitHandle.WaitOne(5000, $false)) {
        $client.Close()
        throw "Connection timeout."
    }

    $client.EndConnect($async)
    $client.Close()

    Write-Host "[OK] TCP Port $Port is reachable."
}
catch {
    throw "Unable to connect to SQL Server on port $Port. $($_.Exception.Message)"
}

# =====================================
# VALIDATE SQLCMD
# =====================================

$sqlcmd = Get-Command sqlcmd -ErrorAction SilentlyContinue

if (!$sqlcmd) {
    throw "sqlcmd utility not found in PATH."
}

Write-Host "[OK] sqlcmd found."

# =====================================
# VALIDATE DATABASE CONNECTION
# =====================================

$query = @"
SELECT
@@SERVERNAME,
@@VERSION,
DB_NAME();
"@

$result = sqlcmd `
    -S "$Server,$Port" `
    -U $User `
    -P $Password `
    -d "master" `
    -Q $query `
    -h -1 `
    -W

if ($LASTEXITCODE -ne 0) {
    throw "Instance connection failed."
}

Write-Host ""
Write-Host "[OK] Instance connection successful."
Write-Host ""

Write-Host $result

# =====================================
# SUCCESS
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "VALIDATION SUCCESSFUL"
Write-Host "====================================="
Write-Host ""

Write-Host "Server   : $Server"
Write-Host "Port     : $Port"
Write-Host "Database : $Database"
Write-Host "Instance : $Instance"

Write-Host ""
Write-Host "[SUCCESS] MSSQL validation completed successfully."
Write-Host ""

exit 0