$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

function Get-ProjectRoot {
    $Root = Split-Path $PSScriptRoot -Parent
    $Root = Split-Path $Root -Parent
    return $Root
}

$ProjectRoot = Get-ProjectRoot

Write-Log "Project Root: $ProjectRoot"

# Read driver version from config
$ConfigFile = Join-Path $ProjectRoot "config\postgresql.conf"
$Config = @{}
if (Test-Path $ConfigFile) {
    Get-Content $ConfigFile | ForEach-Object {
        if ($_ -match "^([^#=]+)=(.*)$") {
            $Config[$Matches[1].Trim()] = $Matches[2].Trim()
        }
    }
}

$DriverVersion = $Config["POSTGRESQL_DRIVER_VERSION"]
if (!$DriverVersion) { $DriverVersion = "42.7.3" }

$DriversDir = Join-Path $ProjectRoot "tools\drivers"
$DriverFile = Join-Path $DriversDir "postgresql-$DriverVersion.jar"

# Check if already downloaded
if (Test-Path $DriverFile) {
    Write-Log "PostgreSQL JDBC driver already present: $DriverFile"
    exit 0
}

# Also check for any postgresql jar (version-independent)
$ExistingJar = Get-ChildItem -Path $DriversDir -Filter "postgresql*.jar" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($ExistingJar) {
    Write-Log "PostgreSQL JDBC driver already present: $($ExistingJar.FullName)"
    exit 0
}

if (!(Test-Path $DriversDir)) {
    New-Item -ItemType Directory -Path $DriversDir -Force | Out-Null
}

$DownloadUrl = "https://jdbc.postgresql.org/download/postgresql-$DriverVersion.jar"

Write-Log "Downloading PostgreSQL JDBC driver v$DriverVersion..."
Write-Log "URL: $DownloadUrl"

try {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    Invoke-WebRequest `
        -Uri     $DownloadUrl `
        -OutFile $DriverFile `
        -TimeoutSec 120

    Write-Log "Driver downloaded: $DriverFile"

} catch {

    Write-Log "Download failed: $_"
    Write-Log ""
    Write-Log "MANUAL ACTION:"
    Write-Log "Download from: $DownloadUrl"
    Write-Log "Save to: $DriverFile"
    exit 1
}

Write-Log "PostgreSQL JDBC driver installation complete"
