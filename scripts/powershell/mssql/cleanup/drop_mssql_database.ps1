$ErrorActionPreference = "Stop"
$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
. "$PROJECT_ROOT\scripts\powershell\common\load_config.ps1"
$Config = Load-Config "$PROJECT_ROOT\config\windows\mssql.conf"

if ($env:CLEANUP_MODE -ne "DELETE_DATA") { exit 0 }

& "$PSScriptRoot\..\ensure_mssql_ready.ps1" -StartIfStopped

$Server = $Config["MSSQL_HOST"]; $Port = $Config["MSSQL_PORT"]; $Database = $Config["MSSQL_DB"]
$User = $Config["MSSQL_USER"]; $Password = $Config["MSSQL_PASSWORD"]
foreach ($entry in @(@("MSSQL_HOST", $Server), @("MSSQL_PORT", $Port), @("MSSQL_DB", $Database), @("MSSQL_USER", $User))) {
    if ([string]::IsNullOrWhiteSpace($entry[1])) { throw "$($entry[0]) is not configured." }
}
$Sqlcmd = Get-Command sqlcmd -ErrorAction SilentlyContinue
if (!$Sqlcmd) { throw "sqlcmd utility not found in PATH." }
function Invoke-Mssql([string]$Query) {
    $output = & $Sqlcmd.Source -S "$Server,$Port" -U $User -P $Password -d master -C -b -h -1 -W -Q $Query 2>&1
    if ($LASTEXITCODE -ne 0) { throw "SQL Server command failed:`n$($output -join [Environment]::NewLine)" }
    return $output
}
$db = $Database.Replace("'", "''")
$before = @(Invoke-Mssql "SET NOCOUNT ON; SELECT physical_name FROM sys.master_files WHERE database_id = DB_ID(N'$db') ORDER BY file_id;" | Where-Object { ![string]::IsNullOrWhiteSpace($_) })
Write-Host "Database files before cleanup:"; $before | Write-Host
$drop = "DECLARE @db sysname=N'$db'; IF DB_ID(@db) IS NOT NULL BEGIN DECLARE @command nvarchar(max) = N'ALTER DATABASE ' + QUOTENAME(@db) + N' SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE ' + QUOTENAME(@db) + N';'; EXEC(@command); END;"
Invoke-Mssql $drop | Write-Host
$databaseCount = (Invoke-Mssql "SET NOCOUNT ON; SELECT COUNT(*) FROM sys.databases WHERE name=N'$db';" -join "").Trim()
$masterFileCount = (Invoke-Mssql "SET NOCOUNT ON; SELECT COUNT(*) FROM sys.master_files WHERE database_id = DB_ID(N'$db');" -join "").Trim()
if ($databaseCount -ne "0" -or $masterFileCount -ne "0") { throw "Database removal verification failed. sys.databases=$databaseCount; sys.master_files=$masterFileCount" }

foreach ($physicalFile in $before) {
    if (Test-Path -LiteralPath $physicalFile) { throw "Physical database file remains after DROP DATABASE: $physicalFile" }
}
Write-Host "MSSQL database removed through DROP DATABASE."
