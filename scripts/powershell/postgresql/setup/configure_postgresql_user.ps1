$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "CONFIGURING POSTGRESQL USER"
Write-Host "====================================="
Write-Host ""

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
$ConfigFile = "$ROOT\config\windows\postgresql.conf"

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

$PgHost = $Config["POSTGRESQL_HOST"]
$PgPort = $Config["POSTGRESQL_PORT"]
$PgDatabase = $Config["POSTGRESQL_DB"]
$PgUser = $Config["POSTGRESQL_USER"]
$PgPassword = $Config["POSTGRESQL_PASSWORD"]

if (-not $PgUser) {
    throw "POSTGRESQL_USER not found in postgresql.conf"
}

if (-not $PgPassword) {
    throw "POSTGRESQL_PASSWORD not found in postgresql.conf"
}

Write-Host "Project Root : $ROOT"
Write-Host "Host         : $PgHost"
Write-Host "Port         : $PgPort"
Write-Host "Database     : $PgDatabase"
Write-Host "User         : $PgUser"
Write-Host ""

$WorkspacePsqlExe = Join-Path $ROOT "databases\postgresql\bin\psql.exe"
$PsqlExe = $null

if (Test-Path -LiteralPath $WorkspacePsqlExe -PathType Leaf) {
    $PsqlExe = (Resolve-Path -LiteralPath $WorkspacePsqlExe).Path
}
else {
    $ServiceName = "PostgreSQLAutomation"
    $ServiceImagePath = Get-CimInstance `
        Win32_Service `
        -Filter "Name='$ServiceName'" `
        -ErrorAction SilentlyContinue

    if ($ServiceImagePath -and $ServiceImagePath.PathName) {

        $PgCtlMatch = [regex]::Match(
            $ServiceImagePath.PathName.Trim(),
            '"?(?<path>[A-Za-z]:\\[^"\r\n]*?\\pg_ctl\.exe)"?',
            [System.Text.RegularExpressions.RegexOptions]::IgnoreCase
        )

        if ($PgCtlMatch.Success) {

            $ServicePgCtl = $PgCtlMatch.Groups['path'].Value.Trim('"')

            if (Test-Path -LiteralPath $ServicePgCtl -PathType Leaf) {
                Write-Host "Resolved pg_ctl.exe from service: $ServicePgCtl"
                $PsqlExe = Join-Path (Split-Path -Parent $ServicePgCtl) "psql.exe"
            }
        }
    }

    if ($PsqlExe -and (Test-Path -LiteralPath $PsqlExe -PathType Leaf)) {
        Write-Host "Resolved psql.exe from service: $PsqlExe"
    }
}

if (-not $PsqlExe -or -not (Test-Path -LiteralPath $PsqlExe -PathType Leaf)) {
    throw "psql.exe not found in workspace: $WorkspacePsqlExe. Unable to resolve it from the PostgreSQLAutomation service."
}

Write-Host "psql.exe     : $PsqlExe"
Write-Host ""

Write-Host "Checking whether user exists..."

$env:PGPASSWORD = $PgPassword

$UserExistsOutput = & $PsqlExe `
    --host="$PgHost" `
    --port="$PgPort" `
    --username=postgres `
    --dbname="postgres" `
    --command="SELECT COUNT(*) FROM pg_roles WHERE rolname='${PgUser}';" `
    2>&1 | Out-String

$env:PGPASSWORD = $null

$UserExists = ($UserExistsOutput -replace '[^\d]', '')

if ([int]$UserExists -gt 0) {

    Write-Host "User '$PgUser' already exists."
    Write-Host "Skipping user creation."

}
else {

    Write-Host "Creating user '$PgUser'..."

    $env:PGPASSWORD = $PgPassword

    & $PsqlExe `
        --host="$PgHost" `
        --port="$PgPort" `
        --username=postgres `
        --dbname="postgres" `
        --command="CREATE USER \"${PgUser}\" WITH PASSWORD '${PgPassword}';" `
        2>&1 | Out-Null

    & $PsqlExe `
        --host="$PgHost" `
        --port="$PgPort" `
        --username=postgres `
        --dbname="postgres" `
        --command="GRANT ALL PRIVILEGES ON DATABASE ${PgDatabase} TO \"${PgUser}\";" `
        2>&1 | Out-Null

    $env:PGPASSWORD = $null

    Write-Host "User created successfully."

}

Write-Host ""
Write-Host "====================================="
Write-Host "POSTGRESQL USER CONFIGURED SUCCESSFULLY"
Write-Host "====================================="
Write-Host ""

exit 0