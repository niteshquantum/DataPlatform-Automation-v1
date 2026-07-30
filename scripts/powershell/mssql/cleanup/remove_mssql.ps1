$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "REMOVING PROJECT-MANAGED MSSQL"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

# =====================================
# LOAD CONFIG
# =====================================

. "$PROJECT_ROOT\scripts\powershell\common\load_config.ps1"

$Config = Load-Config "$PROJECT_ROOT\config\windows\mssql.conf"

$Instance = $Config["MSSQL_INSTANCE"]
$Features = $Config["MSSQL_FEATURES"]
$Database = $Config["MSSQL_DB"]
$AcceptEula = $Config["MSSQL_ACCEPT_EULA"]

if ([string]::IsNullOrWhiteSpace($Instance)) {
    throw "MSSQL_INSTANCE is missing in config/windows/mssql.conf"
}

if ([string]::IsNullOrWhiteSpace($Features)) {
    throw "MSSQL_FEATURES is missing in config/windows/mssql.conf"
}

if ($AcceptEula -notin @("True", "true", "1")) {
    throw "MSSQL_ACCEPT_EULA must explicitly accept the SQL Server license terms for unattended removal."
}

# =====================================
# CLEANUP MODE
# =====================================

$CleanupMode = $env:CLEANUP_MODE

if ([string]::IsNullOrWhiteSpace($CleanupMode)) {
    throw "CLEANUP_MODE environment variable is not set."
}

$CleanupMode = $CleanupMode.Trim().ToUpperInvariant()

if ($CleanupMode -notin @("PRESERVE_DATA", "DELETE_DATA")) {
    throw "Invalid CLEANUP_MODE: $CleanupMode"
}

# =====================================
# SERVICE NAME
# =====================================

if ($Instance -eq "MSSQLSERVER") {
    $ServiceName = "MSSQLSERVER"
}
else {
    $ServiceName = "MSSQL`$$Instance"
}

Write-Host "Project Root : $PROJECT_ROOT"
Write-Host "Instance     : $Instance"
Write-Host "Service Name : $ServiceName"
Write-Host "Features     : $Features"
Write-Host "Database     : $Database"
Write-Host "Cleanup Mode : $CleanupMode"
Write-Host ""

# =====================================
# CHECK INSTANCE
# =====================================

$Service = Get-Service `
    -Name $ServiceName `
    -ErrorAction SilentlyContinue

$InstanceRegistry = Get-ItemProperty `
    -Path "HKLM:\SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL" `
    -ErrorAction SilentlyContinue
$InstanceRegistered = $null -ne $InstanceRegistry -and $null -ne $InstanceRegistry.PSObject.Properties[$Instance]

if ($Service -and !$InstanceRegistered) {
    Write-Host "Removing orphaned SQL Server service '$ServiceName' left by a prior incomplete uninstall."
    & sc.exe delete $ServiceName | Write-Host
    if ($LASTEXITCODE -ne 0) { throw "Unable to remove orphaned SQL Server service '$ServiceName'." }
    $Service = $null
}

if (!$Service) {

    Write-Host "Configured MSSQL instance is not installed."
    Write-Host "Nothing to remove."
    Write-Host ""

    exit 0
}

# =====================================
# PRESERVE DATA MODE
# =====================================

if ($CleanupMode -eq "PRESERVE_DATA") {

    Write-Host "Applying PRESERVE_DATA cleanup..."
    Write-Host ""

    Write-Host "Configured MSSQL instance will be preserved."
    Write-Host "MSSQL database data will be preserved."
    Write-Host ""

    Write-Host "====================================="
    Write-Host "MSSQL DEPLOYMENT PRESERVED"
    Write-Host "====================================="
    Write-Host ""

    exit 0
}

# =====================================
# DELETE DATA MODE
# =====================================

Write-Host "Applying DELETE_DATA cleanup..."
Write-Host ""

# =====================================
# FIND SQL SERVER ISO
# =====================================

$Iso = Get-ChildItem `
    -Path "$PROJECT_ROOT\databases\mssql\media" `
    -Filter "*.iso" `
    -Recurse `
    -ErrorAction SilentlyContinue |
    Select-Object -First 1

if (!$Iso) {
    throw "SQL Server ISO not found. Unable to uninstall MSSQL instance."
}

$IsoPath = $Iso.FullName

Write-Host "SQL Server ISO found:"
Write-Host $IsoPath
Write-Host ""

# =====================================
# MOUNT ISO
# =====================================

Write-Host "Mounting SQL Server ISO..."
Write-Host ""

$DiskImage = Get-DiskImage `
    -ImagePath $IsoPath `
    -ErrorAction SilentlyContinue

if (!$DiskImage.Attached) {

    Mount-DiskImage `
        -ImagePath $IsoPath `
        -StorageType ISO `
        -ErrorAction Stop

    Start-Sleep -Seconds 5
}

# =====================================
# FIND SETUP.EXE
# =====================================

$Drive = Get-DiskImage `
    -ImagePath $IsoPath |
    Get-Volume

if (!$Drive) {
    throw "Unable to detect mounted SQL Server ISO."
}

$SetupExe = Join-Path ($Drive.DriveLetter + ":\") "setup.exe"

if (!(Test-Path $SetupExe)) {
    throw "SQL Server setup.exe not found: $SetupExe"
}

Write-Host "Setup Path : $SetupExe"
Write-Host ""

# =====================================
# UNINSTALL MSSQL INSTANCE
# =====================================

Write-Host "Uninstalling configured MSSQL instance..."
Write-Host ""

$Arguments = @(
    "/Q"
    "/ACTION=Uninstall"
    "/INSTANCENAME=$Instance"
    "/FEATURES=$Features"
    "/IACCEPTSQLSERVERLICENSETERMS"
)

$Process = Start-Process `
    -FilePath $SetupExe `
    -ArgumentList $Arguments `
    -Wait `
    -PassThru

if (
    $Process.ExitCode -ne 0 -and
    $Process.ExitCode -ne 3010
) {
    throw "MSSQL uninstall failed. Exit Code: $($Process.ExitCode)"
}

Write-Host "MSSQL uninstall command completed successfully."
Write-Host ""

# =====================================
# UNMOUNT ISO
# =====================================

Write-Host "Unmounting SQL Server ISO..."
Write-Host ""

Dismount-DiskImage `
    -ImagePath $IsoPath `
    -ErrorAction SilentlyContinue

# =====================================
# VALIDATE INSTANCE REMOVAL
# =====================================

Write-Host "Validating MSSQL instance removal..."
Write-Host ""

$ServiceRemoved = $false

for ($i = 1; $i -le 30; $i++) {

    $Service = Get-Service `
        -Name $ServiceName `
        -ErrorAction SilentlyContinue

    if (!$Service) {
        $ServiceRemoved = $true
        break
    }

    Start-Sleep -Seconds 2
}

if (!$ServiceRemoved) {
    throw "MSSQL instance removal could not be validated."
}

Write-Host "Configured MSSQL instance removed successfully."

Write-Host ""
Write-Host "====================================="
Write-Host "MSSQL DEPLOYMENT REMOVAL COMPLETE"
Write-Host "====================================="
Write-Host ""
Write-Host "Cleanup Mode : $CleanupMode"
Write-Host ""

exit 0
