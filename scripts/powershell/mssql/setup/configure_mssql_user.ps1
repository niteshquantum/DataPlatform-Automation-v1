$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "CONFIGURING MSSQL USER"
Write-Host "====================================="
Write-Host ""

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$ConfigFile = "$ROOT\config\windows\mssql.conf"

if (!(Test-Path $ConfigFile)) {
    throw "Config file not found: $ConfigFile"
}

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

$MssqlHost = $Config["MSSQL_HOST"]
$MssqlPort = $Config["MSSQL_PORT"]
$MssqlUser = $Config["MSSQL_USER"]
$MssqlPassword = $Config["MSSQL_PASSWORD"]

if (-not $MssqlUser) {
    throw "MSSQL_USER not found in mssql.conf"
}

if (-not $MssqlPassword) {
    throw "MSSQL_PASSWORD not found in mssql.conf"
}

Write-Host "Project Root : $ROOT"
Write-Host "Host         : $MssqlHost"
Write-Host "Port         : $MssqlPort"
Write-Host "User         : $MssqlUser"
Write-Host ""

$Sqlcmd = Get-Command sqlcmd -ErrorAction SilentlyContinue

if (-not $Sqlcmd) {
    throw "sqlcmd utility not found in PATH."
}

Write-Host "sqlcmd       : $($Sqlcmd.Source)"
Write-Host ""

Write-Host "Checking whether login exists..."

$LoginExistsOutput = & $Sqlcmd.Source `
    -S "$MssqlHost,$MssqlPort" `
    -U sa `
    -P "$MssqlPassword" `
    -C `
    -Q "SELECT COUNT(*) FROM sys.server_principals WHERE name='${MssqlUser}';" `
    -h -1 -W `
    2>&1 | Out-String

$LoginExists = ($LoginExistsOutput -replace '[^\d]', '')

if ([int]$LoginExists -gt 0) {

    Write-Host "Login '$MssqlUser' already exists."
    Write-Host "Skipping login creation."

}
else {

    Write-Host "Creating login '$MssqlUser'..."

    & $Sqlcmd.Source `
        -S "$MssqlHost,$MssqlPort" `
        -U sa `
        -P "$MssqlPassword" `
        -C `
        -Q "CREATE LOGIN [${MssqlUser}] WITH PASSWORD = '${MssqlPassword}';" `
        -b

    & $Sqlcmd.Source `
        -S "$MssqlHost,$MssqlPort" `
        -U sa `
        -P "$MssqlPassword" `
        -C `
        -Q "ALTER SERVER ROLE sysadmin ADD MEMBER [${MssqlUser}];" `
        -b

    Write-Host "Login created successfully."

}

Write-Host ""
Write-Host "====================================="
Write-Host "MSSQL USER CONFIGURED SUCCESSFULLY"
Write-Host "====================================="
Write-Host ""

exit 0