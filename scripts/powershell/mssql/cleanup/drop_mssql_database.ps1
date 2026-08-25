$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Mssql-CleanupSafety.ps1"
if ($env:CLEANUP_MODE -ne 'DELETE_DATA') { exit 0 }
$context = Get-MssqlCleanupContext
if (-not (Test-MssqlProjectManaged $context)) { Write-Host 'No verified project-managed MSSQL deployment was found. Database is not touched.'; exit 0 }
& "$PSScriptRoot\..\ensure_mssql_ready.ps1" -StartIfStopped
$sqlcmd = Get-Command sqlcmd -ErrorAction Stop
$server = $context.Config['MSSQL_HOST']; $port = $context.Config['MSSQL_PORT']; $user = $context.Config['MSSQL_USER']; $password = $context.Config['MSSQL_PASSWORD']; $database = $context.Config['MSSQL_DB']
foreach ($entry in @(@('MSSQL_HOST', $server), @('MSSQL_PORT', $port), @('MSSQL_USER', $user), @('MSSQL_DB', $database))) { if ([string]::IsNullOrWhiteSpace($entry[1])) { throw "$($entry[0]) is not configured." } }
function Invoke-Mssql([string]$query) { $output = & $sqlcmd.Source -S "$server,$port" -U $user -P $password -d master -C -b -h -1 -W -Q $query 2>&1; if ($LASTEXITCODE -ne 0) { throw "SQL Server command failed: $($output -join [Environment]::NewLine)" }; return @($output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) }
$escapedDatabase = $database.Replace("'", "''")
$files = Invoke-Mssql "SET NOCOUNT ON; SELECT physical_name FROM sys.master_files WHERE database_id = DB_ID(N'$escapedDatabase') ORDER BY file_id;"
foreach ($file in $files) { $fullFile = [System.IO.Path]::GetFullPath($file.Trim()); $dataPrefix = $context.DataDir.TrimEnd('\') + '\'; if (-not $fullFile.StartsWith($dataPrefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Refusing to drop database because a file is outside MSSQL_DATA_DIR: $fullFile" } }
$query = "DECLARE @db sysname=N'$escapedDatabase'; IF DB_ID(@db) IS NOT NULL BEGIN DECLARE @sql nvarchar(max)=N'ALTER DATABASE '+QUOTENAME(@db)+N' SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE '+QUOTENAME(@db)+N';'; EXEC(@sql); END;"
Invoke-Mssql $query | Write-Host
if ((Invoke-Mssql "SET NOCOUNT ON; SELECT COUNT(*) FROM sys.databases WHERE name=N'$escapedDatabase';" -join '').Trim() -ne '0') { throw 'Database removal verification failed.' }
Write-Host 'Project-managed MSSQL database was removed.'
