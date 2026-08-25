$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Mssql-CleanupSafety.ps1"
if ($env:CLEANUP_MODE -ne 'DELETE_DATA') { exit 0 }
$context = Get-MssqlCleanupContext
& "$PSScriptRoot\..\ensure_mssql_ready.ps1" -StartIfStopped
$sqlcmd = Get-Command sqlcmd -ErrorAction Stop
$server = $context.Config['MSSQL_HOST']; $port = $context.Config['MSSQL_PORT']; $user = $context.Config['MSSQL_USER']; $password = $context.Config['MSSQL_PASSWORD']; $database = $context.Config['MSSQL_DB']
foreach ($entry in @(@('MSSQL_HOST', $server), @('MSSQL_PORT', $port), @('MSSQL_USER', $user), @('MSSQL_DB', $database))) { if ([string]::IsNullOrWhiteSpace($entry[1])) { throw "$($entry[0]) is not configured." } }
if ($database -notmatch '^[A-Za-z0-9_]+$') { throw "MSSQL_DB must contain only letters, numbers, and underscores for safe file cleanup." }
function Invoke-Mssql([string]$query) { $output = & $sqlcmd.Source -S "$server,$port" -U $user -P $password -d master -C -b -h -1 -W -Q $query 2>&1; if ($LASTEXITCODE -ne 0) { throw "SQL Server command failed: $($output -join [Environment]::NewLine)" }; return @($output | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) }
$escapedDatabase = $database.Replace("'", "''")
$defaultDataDirectory = (Invoke-Mssql "SET NOCOUNT ON; SELECT CONVERT(nvarchar(4000), SERVERPROPERTY('InstanceDefaultDataPath'));" -join "").Trim()
if ([string]::IsNullOrWhiteSpace($defaultDataDirectory)) { throw 'SQL Server did not report an InstanceDefaultDataPath.' }

$defaultDataDirectory = [System.IO.Path]::GetFullPath($defaultDataDirectory)
$dataPrefix = $defaultDataDirectory.TrimEnd('\') + '\'
$expectedMdf = [System.IO.Path]::GetFullPath((Join-Path $defaultDataDirectory "$database.mdf"))
$expectedLdf = [System.IO.Path]::GetFullPath((Join-Path $defaultDataDirectory "${database}_log.ldf"))
foreach ($expectedFile in @($expectedMdf, $expectedLdf)) {
    if (-not $expectedFile.StartsWith($dataPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clean a file outside the active SQL Server default data directory: $expectedFile"
    }
}

$databaseExists = ((Invoke-Mssql "SET NOCOUNT ON; SELECT CASE WHEN DB_ID(N'$escapedDatabase') IS NULL THEN 0 ELSE 1 END;" -join '').Trim() -eq '1')
if ($databaseExists) {
    $databaseFiles = Invoke-Mssql "SET NOCOUNT ON; SELECT physical_name FROM sys.master_files WHERE database_id = DB_ID(N'$escapedDatabase') ORDER BY file_id;"
    if ($databaseFiles.Count -ne 2) { throw "Refusing to drop $database because it does not have exactly the expected MDF and LDF files." }

    foreach ($file in $databaseFiles) {
        $fullFile = [System.IO.Path]::GetFullPath($file.Trim())
        if ($fullFile -ne $expectedMdf -and $fullFile -ne $expectedLdf) {
            throw "Refusing to drop $database because it references an unexpected file: $fullFile"
        }
    }

    $query = "DECLARE @db sysname=N'$escapedDatabase'; DECLARE @sql nvarchar(max)=N'ALTER DATABASE '+QUOTENAME(@db)+N' SET SINGLE_USER WITH ROLLBACK IMMEDIATE; DROP DATABASE '+QUOTENAME(@db)+N';'; EXEC(@sql);"
    Invoke-Mssql $query | Write-Host
}

if ((Invoke-Mssql "SET NOCOUNT ON; SELECT COUNT(*) FROM sys.databases WHERE name=N'$escapedDatabase';" -join '').Trim() -ne '0') { throw 'Database removal verification failed.' }

$escapedMdf = $expectedMdf.Replace("'", "''")
$escapedLdf = $expectedLdf.Replace("'", "''")
$registeredFiles = Invoke-Mssql "SET NOCOUNT ON; SELECT DB_NAME(database_id) + N'|' + physical_name FROM sys.master_files WHERE physical_name IN (N'$escapedMdf', N'$escapedLdf');"
if ($registeredFiles.Count -ne 0) { throw "Refusing to remove configured database files because they are registered to a database: $($registeredFiles -join '; ')" }

foreach ($orphanFile in @($expectedMdf, $expectedLdf)) {
    if (Test-Path -LiteralPath $orphanFile) {
        $item = Get-Item -LiteralPath $orphanFile -Force -ErrorAction Stop
        if ($item.PSIsContainer) { throw "Refusing to remove a directory at the expected database file path: $orphanFile" }
        Remove-Item -LiteralPath $orphanFile -Force -ErrorAction Stop
    }
}

foreach ($orphanFile in @($expectedMdf, $expectedLdf)) {
    if (Test-Path -LiteralPath $orphanFile) { throw "Database file removal verification failed: $orphanFile" }
}

Write-Host 'Configured MSSQL database and its exact orphaned data files were removed.'
