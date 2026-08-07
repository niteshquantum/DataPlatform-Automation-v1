$ErrorActionPreference = "Stop"

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path
. "$PROJECT_ROOT\scripts\powershell\common\load_config.ps1"
$Config = Load-Config "$PROJECT_ROOT\config\windows\mssql.conf"

$Server = $Config["MSSQL_HOST"]
$Port = $Config["MSSQL_PORT"]
$Database = $Config["MSSQL_DB"]
$User = $Config["MSSQL_USER"]
$Password = $Config["MSSQL_PASSWORD"]

foreach ($entry in @(@("MSSQL_HOST", $Server), @("MSSQL_PORT", $Port), @("MSSQL_DB", $Database), @("MSSQL_USER", $User))) {
    if ([string]::IsNullOrWhiteSpace($entry[1])) { throw "$($entry[0]) is not configured." }
}

$Sqlcmd = Get-Command sqlcmd -ErrorAction SilentlyContinue
if (!$Sqlcmd) { throw "sqlcmd utility not found in PATH." }

function Invoke-Mssql {
    param([string]$Query)
    $output = & $Sqlcmd.Source -S "$Server,$Port" -U $User -P $Password -d master -C -b -W -Q $Query 2>&1
    if ($LASTEXITCODE -ne 0) { throw "SQL Server command failed:`n$($output -join [Environment]::NewLine)" }
    return $output
}

$DatabaseLiteral = $Database.Replace("'", "''")
$UserLiteral = $User.Replace("'", "''")

Write-Host ""
Write-Host "====================================="
Write-Host "CREATE DATABASE"
Write-Host "====================================="
Write-Host ""
Write-Host "Host     : $Server"
Write-Host "Port     : $Port"
Write-Host "Database : $Database"
Write-Host "User     : $User"
Write-Host ""

$provisionQuery = @"
SET NOCOUNT ON;
DECLARE @Database sysname = N'$DatabaseLiteral';
DECLARE @Owner sysname = N'$UserLiteral';

IF DB_ID(@Database) IS NULL
BEGIN
    DECLARE @Command nvarchar(max);

    SET @Command =
        N'CREATE DATABASE ' + QUOTENAME(@Database);

    EXEC(@Command);
END

IF (SELECT state_desc FROM sys.databases WHERE name = @Database) <> N'ONLINE'
    THROW 50002, 'Database exists but is not ONLINE.', 1;

IF SUSER_ID(@Owner) IS NULL THROW 50003, 'Configured database owner login does not exist.', 1;
IF (SELECT SUSER_SNAME(owner_sid) FROM sys.databases WHERE name = @Database) <> @Owner
BEGIN
    DECLARE @OwnerCommand nvarchar(max) = N'ALTER AUTHORIZATION ON DATABASE::' + QUOTENAME(@Database) + N' TO ' + QUOTENAME(@Owner) + N';';
    EXEC (@OwnerCommand);
END

DECLARE @ExpectedCompatibility int = (SELECT compatibility_level FROM sys.databases WHERE name = N'master');
IF (SELECT compatibility_level FROM sys.databases WHERE name = @Database) <> @ExpectedCompatibility
BEGIN
    DECLARE @CompatibilityCommand nvarchar(max) = N'ALTER DATABASE ' + QUOTENAME(@Database) + N' SET COMPATIBILITY_LEVEL = ' + CONVERT(nvarchar(10), @ExpectedCompatibility) + N';';
    EXEC (@CompatibilityCommand);
END

SELECT name, state_desc, SUSER_SNAME(owner_sid) AS owner_name, compatibility_level
FROM sys.databases WHERE name = @Database;
SELECT physical_name FROM sys.master_files WHERE database_id = DB_ID(@Database) ORDER BY file_id;
"@

Invoke-Mssql $provisionQuery | Write-Host

$accessQuery = "SET NOCOUNT ON; USE [$($Database.Replace(']', ']]'))]; SELECT DB_NAME() AS database_name;"
$accessOutput = Invoke-Mssql $accessQuery
if (($accessOutput -join "`n") -notmatch [regex]::Escape($Database)) { throw "Database accessibility verification failed." }

Write-Host ""
Write-Host "====================================="
Write-Host "DATABASE READY"
Write-Host "====================================="
Write-Host ""
Write-Host "[SUCCESS] Database creation or reuse completed successfully."
