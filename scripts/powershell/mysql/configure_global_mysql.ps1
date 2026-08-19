$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

$configFile = "$ROOT\config\windows\mysql.conf"

if (!(Test-Path $configFile)) {
    throw "Config file not found: $configFile"
}

# =====================================
# READ CONFIG
# =====================================

$config = @{}

Get-Content $configFile | ForEach-Object {

    if ($_ -match "^([^#][^=]*)=(.*)$") {

        $key = $matches[1].Trim()
        $value = $matches[2].Trim()

        $config[$key] = $value
    }
}

$hostName = $config["MYSQL_HOST"]
$port     = $config["MYSQL_PORT"]
$database = $config["MYSQL_DB"]
$user     = $config["MYSQL_USER"]
$password = $config["MYSQL_PASSWORD"]

$WorkspaceMySQLExe = Join-Path $ROOT "databases\mysql\server\bin\mysql.exe"
$mysqlExe = $null

if (Test-Path -LiteralPath $WorkspaceMySQLExe -PathType Leaf) {
    $mysqlExe = (Resolve-Path -LiteralPath $WorkspaceMySQLExe).Path
}
else {
    $ServiceName = "MySQLAutomation"
    $ServiceImagePath = Get-CimInstance `
        Win32_Service `
        -Filter "Name='$ServiceName'" `
        -ErrorAction SilentlyContinue

    if ($ServiceImagePath -and $ServiceImagePath.PathName) {

        $MysqldMatch = [regex]::Match(
            $ServiceImagePath.PathName.Trim(),
            '"?(?<path>[A-Za-z]:\\[^"\r\n]*?\\mysqld\.exe)"?',
            [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
        )

        if ($MysqldMatch.Success) {

            $MysqldPath = $MysqldMatch.Groups['path'].Value.Trim('"')

            if (Test-Path -LiteralPath $MysqldPath -PathType Leaf) {

                $ResolvedMySQLExe = Join-Path (Split-Path -Parent $MysqldPath) "mysql.exe"

                if (Test-Path -LiteralPath $ResolvedMySQLExe -PathType Leaf) {
                    $mysqlExe = (Resolve-Path -LiteralPath $ResolvedMySQLExe).Path
                    Write-Host "Resolved mysql.exe from existing MySQL service: $mysqlExe"
                }
            }
        }
    }
}

if (-not $mysqlExe) {
    throw "mysql.exe not found in workspace: $WorkspaceMySQLExe. Unable to resolve it from the MySQLAutomation service."
}

Write-Host "MySQL Client : $mysqlExe"
Write-Host "Host         : $hostName"
Write-Host "Port         : $port"
Write-Host "Database     : $database"
Write-Host "User         : $user"

# =====================================
# ADD MYSQL BIN DIRECTORY TO SYSTEM PATH
# =====================================

$mysqlBinDirectory = Split-Path -Parent $mysqlExe

$machinePath = [Environment]::GetEnvironmentVariable(
    "Path",
    "Machine"
)

$pathEntries = $machinePath -split ";" |
    Where-Object {
        $_ -and
        $_.Trim().TrimEnd("\") -ne $mysqlBinDirectory.TrimEnd("\")
    }

$newPath = $mysqlBinDirectory + ";" + ($pathEntries -join ";")

[Environment]::SetEnvironmentVariable(
    "Path",
    $newPath,
    "Machine"
)

Write-Host ""
Write-Host "MySQL bin directory added to beginning of System PATH"

# =====================================
# VALIDATE GLOBAL MYSQL COMMAND
# =====================================

$env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")

$mysqlCommand = Get-Command mysql.exe -ErrorAction SilentlyContinue

if (!$mysqlCommand) {
    throw "mysql.exe is not accessible from PATH after configuration"
}

Write-Host ""
Write-Host "====================================="
Write-Host "GLOBAL MYSQL CONFIGURED SUCCESSFULLY"
Write-Host "====================================="
Write-Host ""
Write-Host "MySQL client has been added to the System PATH."
Write-Host ""
Write-Host "Examples:"
Write-Host ""
Write-Host "    mysql -u root"
Write-Host ""
Write-Host "or"
Write-Host ""
Write-Host "    mysql -u <username>"
Write-Host ""
Write-Host "Open a NEW CMD window before testing."
Write-Host ""
Write-Host "The PATH configuration is complete."
Write-Host "Authentication depends on the MySQL user specified."
Write-Host ""

exit 0
