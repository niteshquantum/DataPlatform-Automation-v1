param(
    [switch]$StartIfStopped,
    [int]$TimeoutSeconds = 60
)

$ErrorActionPreference = "Stop"
$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path
. "$PROJECT_ROOT\scripts\powershell\common\load_config.ps1"
$Config = Load-Config "$PROJECT_ROOT\config\windows\mssql.conf"

$Server = $Config["MSSQL_HOST"]
$Port = $Config["MSSQL_PORT"]
$User = $Config["MSSQL_USER"]
$Password = $Config["MSSQL_PASSWORD"]
$Instance = $Config["MSSQL_INSTANCE"]

foreach ($entry in @(@("MSSQL_HOST", $Server), @("MSSQL_PORT", $Port), @("MSSQL_USER", $User), @("MSSQL_INSTANCE", $Instance))) {
    if ([string]::IsNullOrWhiteSpace($entry[1])) { throw "$($entry[0]) is not configured." }
}

$ServiceName = if ($Instance -eq "MSSQLSERVER") { "MSSQLSERVER" } else { "MSSQL`$$Instance" }
$Service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if (!$Service) { throw "SQL Server service '$ServiceName' was not found." }

if ($Service.Status -ne "Running") {
    if (!$StartIfStopped) { throw "SQL Server service '$ServiceName' is not running." }
    Write-Host "Starting SQL Server service '$ServiceName'..."
    Start-Service -Name $ServiceName -ErrorAction Stop
}

$Service.WaitForStatus([System.ServiceProcess.ServiceControllerStatus]::Running, [TimeSpan]::FromSeconds($TimeoutSeconds))
$Service.Refresh()
if ($Service.Status -ne "Running") { throw "SQL Server service '$ServiceName' did not reach Running state." }

$tcpClient = [System.Net.Sockets.TcpClient]::new()
try {
    $connectTask = $tcpClient.ConnectAsync($Server, [int]$Port)
    if (!$connectTask.Wait([TimeSpan]::FromSeconds($TimeoutSeconds))) {
        throw "SQL Server did not accept TCP connections on $Server`:$Port within $TimeoutSeconds seconds."
    }
    $connectTask.GetAwaiter().GetResult() | Out-Null
}
finally {
    $tcpClient.Dispose()
}

$Sqlcmd = Get-Command sqlcmd -ErrorAction SilentlyContinue
if (!$Sqlcmd) { throw "sqlcmd utility not found in PATH." }
$output = & $Sqlcmd.Source -S "$Server,$Port" -U $User -P $Password -d master -C -b -l $TimeoutSeconds -h -1 -W -Q "SET NOCOUNT ON; SELECT 1;" 2>&1
if ($LASTEXITCODE -ne 0 -or (($output -join "`n").Trim() -ne "1")) {
    throw "SQL Server service is running and TCP is open, but SQL authentication/readiness verification failed: $($output -join [Environment]::NewLine)"
}

Write-Host "[OK] SQL Server service, TCP port $Port, and master connection are ready."
