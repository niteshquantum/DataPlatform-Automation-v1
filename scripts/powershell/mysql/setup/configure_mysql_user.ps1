$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "CONFIGURING MYSQL USER"
Write-Host "====================================="
Write-Host ""

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$ConfigFile = "$ROOT\config\windows\mysql.conf"

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

$MySQLHost = $Config["MYSQL_HOST"]
$MySQLPort = $Config["MYSQL_PORT"]
$MySQLUser = $Config["MYSQL_USER"]
$MySQLPassword = $Config["MYSQL_PASSWORD"]

if (-not $MySQLUser) {
    throw "MYSQL_USER not found in mysql.conf"
}

if (-not $MySQLPassword) {
    throw "MYSQL_PASSWORD not found in mysql.conf"
}

Write-Host "Project Root : $ROOT"
Write-Host "Host         : $MySQLHost"
Write-Host "Port         : $MySQLPort"
Write-Host "User         : $MySQLUser"
Write-Host ""

$MySQLExe = "$ROOT\databases\mysql\server\bin\mysql.exe"

if (!(Test-Path $MySQLExe)) {

    Write-Host "Resolving mysql.exe from existing MySQL service..."

    $ServiceImagePath = Get-CimInstance `
        Win32_Service `
        -Filter "Name='MySQLAutomation'" `
        -ErrorAction SilentlyContinue

    if ($ServiceImagePath -and $ServiceImagePath.PathName) {

        Write-Host "Service PathName:"
        Write-Host $ServiceImagePath.PathName

        # The Windows service contains mysqld.exe.
        # mysql.exe is located in the same bin directory.
        $MysqldMatch = [regex]::Match(
            $ServiceImagePath.PathName.Trim(),
            '"(?<path>[^"]*\\mysqld\.exe)"|(?<path2>[A-Za-z]:\\.*?\\mysqld\.exe)',
            [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
        )

        if ($MysqldMatch.Success) {

            if ($MysqldMatch.Groups['path'].Success) {
                $ServiceMysqld = $MysqldMatch.Groups['path'].Value
            }
            else {
                $ServiceMysqld = $MysqldMatch.Groups['path2'].Value
            }

            Write-Host "Resolved mysqld.exe from service: $ServiceMysqld"

            $MySQLBinDir = Split-Path `
                -Path $ServiceMysqld `
                -Parent

            $ServiceMySQL = Join-Path `
                -Path $MySQLBinDir `
                -ChildPath "mysql.exe"

            Write-Host "Looking for mysql.exe:"
            Write-Host $ServiceMySQL

            if (Test-Path -LiteralPath $ServiceMySQL -PathType Leaf) {

                Write-Host "Resolved mysql.exe from existing MySQL service installation."

                $MySQLExe = $ServiceMySQL
            }
        }
    }

    if (!(Test-Path $MySQLExe)) {
        throw "mysql.exe could not be resolved from the current workspace or the MySQLAutomation service installation."
    }
}

Write-Host "mysql.exe    : $MySQLExe"
Write-Host ""

Write-Host "Checking whether user exists..."

$UserExistsOutput = & $MySQLExe `
    -h "$MySQLHost" `
    -P "$MySQLPort" `
    -u root `
    -e "SELECT COUNT(*) FROM mysql.user WHERE user='${MySQLUser}';" `
    2>&1 | Out-String

$UserExists = ($UserExistsOutput -replace '[^\d]', '')

if ([int]$UserExists -gt 0) {

    Write-Host "User '$MySQLUser' already exists."
    Write-Host "Skipping user creation."

}
else {

    Write-Host "Creating user '$MySQLUser'..."

    $CreateUserSql = @"
CREATE USER '${MySQLUser}'@'localhost'
IDENTIFIED BY '${MySQLPassword}';

GRANT ALL PRIVILEGES
ON *.*
TO '${MySQLUser}'@'localhost'
WITH GRANT OPTION;

FLUSH PRIVILEGES;
"@

    & $MySQLExe `
        -h "$MySQLHost" `
        -P "$MySQLPort" `
        -u root `
        -e $CreateUserSql `
        2>&1 | Out-Null

    Write-Host "User created successfully."

}

Write-Host ""
Write-Host "====================================="
Write-Host "MYSQL USER CONFIGURED SUCCESSFULLY"
Write-Host "====================================="
Write-Host ""

exit 0