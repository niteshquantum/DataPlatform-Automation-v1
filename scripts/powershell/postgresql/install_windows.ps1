$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$Timestamp] $Message"
}

function Get-ProjectRoot {
    $Root = Split-Path $PSScriptRoot -Parent
    $Root = Split-Path $Root -Parent
    $Root = Split-Path $Root -Parent
    return $Root
}

$ProjectRoot     = Get-ProjectRoot
$PgProjectBin    = Join-Path $ProjectRoot "databases\postgresql\bin"
$PgProjectData   = Join-Path $ProjectRoot "databases\postgresql\data"
$PgProjectLib    = Join-Path $ProjectRoot "databases\postgresql\lib"
$PgProjectShare  = Join-Path $ProjectRoot "databases\postgresql\share"

Write-Log "Project Root  : $ProjectRoot"
Write-Log "Project PG Bin: $PgProjectBin"

# Read config
$ConfigFile = Join-Path $ProjectRoot "config\windows\postgresql.conf"
if (!(Test-Path $ConfigFile)) {
    throw "Config not found: $ConfigFile"
}

$Config = @{}
Get-Content $ConfigFile | ForEach-Object {
    if ($_ -match "^([^#=]+)=(.*)$") {
        $Config[$Matches[1].Trim()] = $Matches[2].Trim()
    }
}

$PgHost = $Config["POSTGRESQL_HOST"]

$ExpectedPort = [int]$Config["POSTGRESQL_PORT"]

$PgDatabase = $Config["POSTGRESQL_DB"]

$PgUser = if ([string]::IsNullOrWhiteSpace($Config["POSTGRESQL_USER"])) {
    "postgres"
}
else {
    $Config["POSTGRESQL_USER"]
}

$PgPassword = $Config["POSTGRESQL_PASSWORD"]

$PgVersion = if ([string]::IsNullOrWhiteSpace($Config["POSTGRESQL_VERSION"])) {
    throw "POSTGRESQL_VERSION is missing in config."
}
else {
    $Config["POSTGRESQL_VERSION"]
}

Write-Log "Host               : $PgHost"
Write-Log "Port               : $ExpectedPort"
Write-Log "Database           : $PgDatabase"
Write-Log "User               : $PgUser"
Write-Log "Version            : $PgVersion"

# ---- FAST PATH: binaries AND data directory both ready ----

$BinReady  = Test-Path (Join-Path $PgProjectBin "pg_ctl.exe")
$DataReady = Test-Path (Join-Path $PgProjectData "PG_VERSION")

if ($BinReady -and $DataReady) {

    Write-Log "Project PostgreSQL binaries already exist."
    Write-Log "Project data directory already initialized."
    Write-Log "Skipping installation."

    exit 0
}

# ---- If binaries exist but data not initialized, go straight to initdb ----

if ($BinReady -and !$DataReady) {

    Write-Log "Binaries found but data directory not initialized - running initdb..."

    New-Item -ItemType Directory -Path $PgProjectData -Force | Out-Null

    $env:PATH = "$PgProjectBin;$env:PATH"

    & (Join-Path $PgProjectBin "initdb.exe") `
        -D "$PgProjectData" `
        -U postgres `
        --encoding=UTF8

    if ($LASTEXITCODE -ne 0) {
        throw "initdb failed with exit code $LASTEXITCODE"
    }

    $PgConfFile = Join-Path $PgProjectData "postgresql.conf"

    (Get-Content $PgConfFile) `
        -replace '^#?port\s*=.*', "port = $ExpectedPort" `
        | Set-Content $PgConfFile

    Add-Content $PgConfFile "`nfsync = off"
    Add-Content $PgConfFile "`nsynchronous_commit = off"
    Add-Content $PgConfFile "`nfull_page_writes = off"

    Write-Log "Data directory initialized with dev settings, port = $ExpectedPort"

    exit 0
}

Write-Log "Project folder binaries not found - checking system installation..."

# ---- Check system-installed PostgreSQL ----

$SystemBinPaths = @(
    "C:\Program Files\PostgreSQL\$PgVersion\bin",
    "C:\Program Files\PostgreSQL\17\bin",
    "C:\Program Files\PostgreSQL\16\bin",
    "C:\Program Files\PostgreSQL\15\bin"
)

Write-Log "Searching PostgreSQL Version $PgVersion ..."

$SystemBin = $null

foreach ($BinPath in $SystemBinPaths) {

    if (Test-Path (Join-Path $BinPath "pg_ctl.exe")) {

        $SystemBin = $BinPath
        Write-Log "Found system PostgreSQL at: $SystemBin"
        break
    }
}

if ($SystemBin) {
    Write-Log "System installation found."
}
else {
    Write-Log "System installation not found."
}

# ------------------------------------------------------------
# Use cached ZIP if available
# ------------------------------------------------------------

if (!$SystemBin) {

    $ZipDir  = Join-Path $ProjectRoot "databases\postgresql\zip"
    $ZipFile = Join-Path $ZipDir "postgresql-binaries.zip"
    $ExtDir  = Join-Path $ZipDir "extracted"
    
    New-Item -ItemType Directory -Path $ZipDir -Force | Out-Null

    if (Test-Path $ZipFile) {

        Write-Log "Using cached PostgreSQL ZIP."
    }
    else {

        Write-Log "PostgreSQL ZIP not found - downloading..."

        $ZipUrl = "https://get.enterprisedb.com/postgresql/postgresql-$PgVersion.5-1-windows-x64-binaries.zip"

        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

        Invoke-WebRequest `
            -Uri $ZipUrl `
            -OutFile $ZipFile `
            -UseBasicParsing `
            -TimeoutSec 600

        Write-Log "Download complete."
    }

    Write-Log "Extracting ZIP..."

    if (Test-Path $ExtDir) {

        Write-Log "Removing previous extraction..."

        Remove-Item `
            -Path $ExtDir `
            -Recurse `
            -Force `
            -ErrorAction SilentlyContinue

        Start-Sleep -Seconds 2
    }

    New-Item -ItemType Directory -Path $ExtDir -Force | Out-Null

    Write-Log "Extracting PostgreSQL ZIP using tar..."

    tar -xf "$ZipFile" -C "$ExtDir"

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to extract PostgreSQL ZIP."
    }

    Write-Log "Extraction completed."

    $SystemBin = Join-Path $ExtDir "pgsql\bin"

    if (!(Test-Path (Join-Path $SystemBin "pg_ctl.exe"))) {
        throw "Invalid PostgreSQL binaries extracted."
    }

    Write-Log "Using extracted binaries: $SystemBin"
}

# ---- Copy binaries to project folder ----

Write-Log "Copying binaries from $SystemBin to project folder..."

$SystemRoot = Split-Path $SystemBin -Parent

New-Item -ItemType Directory -Path $PgProjectBin -Force | Out-Null
New-Item -ItemType Directory -Path $PgProjectLib -Force | Out-Null
New-Item -ItemType Directory -Path $PgProjectShare -Force | Out-Null
Copy-Item `
    -Path (Join-Path $SystemRoot "bin\*") `
    -Destination $PgProjectBin `
    -Recurse `
    -Force

Copy-Item `
    -Path (Join-Path $SystemRoot "lib\*") `
    -Destination $PgProjectLib `
    -Recurse `
    -Force

Copy-Item `
    -Path (Join-Path $SystemRoot "share\*") `
    -Destination $PgProjectShare `
    -Recurse `
    -Force

Write-Log "Binaries copied successfully"

if (!(Test-Path (Join-Path $PgProjectBin "pg_ctl.exe"))) {
    throw "pg_ctl.exe not found after copy."
}

if (!(Test-Path (Join-Path $PgProjectBin "postgres.exe"))) {
    throw "postgres.exe not found after copy."
}

if (!(Test-Path (Join-Path $PgProjectBin "initdb.exe"))) {
    throw "initdb.exe not found after copy."
}

if (!(Test-Path (Join-Path $PgProjectBin "psql.exe"))) {
    throw "psql.exe missing."
}

Write-Log "Binary validation successful."

# ---- initdb: initialize project data directory ----

if (!(Test-Path (Join-Path $PgProjectData "PG_VERSION"))) {

    Write-Log "Initializing data directory: $PgProjectData"

    New-Item -ItemType Directory -Path $PgProjectData -Force | Out-Null

    $env:PATH = "$PgProjectBin;$env:PATH"

    & (Join-Path $PgProjectBin "initdb.exe") `
        -D "$PgProjectData" `
        -U postgres `
        --encoding=UTF8

    if ($LASTEXITCODE -ne 0) {
        throw "initdb failed with exit code $LASTEXITCODE"
    }

    $PgConfFile = Join-Path $PgProjectData "postgresql.conf"

    (Get-Content $PgConfFile) `
        -replace '^#?port\s*=.*', "port = $ExpectedPort" `
        | Set-Content $PgConfFile

    Add-Content $PgConfFile "`nfsync = off"
    Add-Content $PgConfFile "`nsynchronous_commit = off"
    Add-Content $PgConfFile "`nfull_page_writes = off"

    Write-Log "Data directory initialized with dev settings, port = $ExpectedPort"
}
else {    Write-Log "Data directory already initialized"
}

Write-Log ""
Write-Log "======================================="
Write-Log "POSTGRESQL INSTALLATION COMPLETED"
Write-Log "======================================="
Write-Log "Version  : $PgVersion"
Write-Log "Host     : $PgHost"
Write-Log "Port     : $ExpectedPort"
Write-Log "Database : $PgDatabase"
Write-Log "User     : $PgUser"
Write-Log "Binaries : $PgProjectBin"
Write-Log "Data Dir : $PgProjectData"

if ([string]::IsNullOrWhiteSpace($PgHost)) {
    throw "POSTGRESQL_HOST is missing in config."
}

if ([string]::IsNullOrWhiteSpace($PgDatabase)) {
    throw "POSTGRESQL_DB is missing in config."
}

if ($ExpectedPort -le 0) {
    throw "Invalid POSTGRESQL_PORT."
}