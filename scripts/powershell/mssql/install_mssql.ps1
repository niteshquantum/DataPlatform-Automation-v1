$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "INSTALLING MSSQL SERVER"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

# =====================================
# LOAD CONFIG
# =====================================

. "$PROJECT_ROOT\scripts\powershell\common\load_config.ps1"

$Config = Load-Config "$PROJECT_ROOT\config\windows\mssql.conf"

$Instance = $Config["MSSQL_INSTANCE"]
$Password = $Config["MSSQL_PASSWORD"]
$Port     = $Config["MSSQL_PORT"]

# =====================================
# SERVICE NAME
# =====================================

if ($Instance -eq "MSSQLSERVER") {
    $ServiceName = "MSSQLSERVER"
}
else {
    $ServiceName = "MSSQL`$$Instance"
}

# =====================================
# CHECK EXISTING INSTALLATION
# =====================================

$Service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($Service) {

    Write-Host "SQL Server instance '$Instance' already installed."

    $sqlcmd = Get-Command sqlcmd -ErrorAction SilentlyContinue

    if (!$sqlcmd) {
        throw "sqlcmd utility not found in PATH. Cannot bootstrap the existing SQL Server instance."
    }

    Write-Host "Applying configured sa password to the existing SQL Server instance..."

    sqlcmd `
        -S "localhost,$Port" `
        -E `
        -C `
        -d master `
        -v SAPWD="$Password" `
        -Q "ALTER LOGIN [sa] ENABLE; ALTER LOGIN [sa] WITH PASSWORD = N'`$(SAPWD)' UNLOCK;"

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to bootstrap the sa login for existing SQL Server instance '$Instance'. Ensure the deployment account is a SQL Server sysadmin."
    }

    Write-Host "Configured sa password applied to existing SQL Server instance."
    exit 0

}

# =====================================
# ISO PATH
# =====================================

# =====================================
# FIND ISO
# =====================================

$Iso = Get-ChildItem `
    -Path "$PROJECT_ROOT\databases\mssql\media" `
    -Filter "*.iso" `
    -Recurse |
    Select-Object -First 1

if (!$Iso) {

    throw "SQL Server ISO not found."

}

$IsoPath = $Iso.FullName

Write-Host "ISO Found"
Write-Host $IsoPath
Write-Host ""

if (!(Test-Path $IsoPath)) {

    throw "SQL Server ISO not found.`n$IsoPath"

}

Write-Host "ISO Found"
Write-Host $IsoPath
Write-Host ""

# =====================================
# MOUNT ISO
# =====================================

Write-Host "Mounting ISO..."
Write-Host ""

Mount-DiskImage `
    -ImagePath $IsoPath `
    -StorageType ISO

Start-Sleep -Seconds 5

# =====================================
# GET DRIVE LETTER
# =====================================

$Drive = Get-DiskImage -ImagePath $IsoPath |
    Get-Volume

$SetupExe = Join-Path ($Drive.DriveLetter + ":\") "setup.exe"

if (!$Drive) {

    throw "Unable to detect mounted SQL Server ISO."

}

Write-Host "Drive Letter : $($Drive.DriveLetter)"
Write-Host "Setup Path   : $SetupExe"

if (!(Test-Path $SetupExe)) {

    throw "setup.exe not found.`n$SetupExe"

}

Write-Host "Setup Found : $SetupExe"
Write-Host ""

Write-Host ""
Write-Host "Generating Configuration File..."
Write-Host ""

& "$PROJECT_ROOT\scripts\powershell\mssql\generate_configuration_file.ps1"

$ConfigurationFile = Join-Path `
    $PROJECT_ROOT `
    "databases\mssql\ConfigurationFile.ini"

if (!(Test-Path $ConfigurationFile)) {
    throw "Configuration file not found.`n$ConfigurationFile"
}

Write-Host "Starting unattended SQL Server installation..."
Write-Host ""

$Arguments = @(
    "/ConfigurationFile=`"$ConfigurationFile`""
)

$Process = Start-Process `
    -FilePath $SetupExe `
    -ArgumentList $Arguments `
    -Wait `
    -PassThru

if ($Process.ExitCode -ne 0 -and $Process.ExitCode -ne 3010) {

    throw "Installation failed. Exit Code : $($Process.ExitCode)"

}

Write-Host ""
Write-Host "Unmounting SQL Server ISO..."
Write-Host ""

Dismount-DiskImage `
    -ImagePath $IsoPath `
    -ErrorAction SilentlyContinue

# =====================================
# VERIFY SERVICE
# =====================================

$Service = $null

for ($i = 1; $i -le 30; $i++) {

    $Service = Get-Service `
        -Name $ServiceName `
        -ErrorAction SilentlyContinue

    if ($Service) {
        break
    }

    Start-Sleep -Seconds 1
}

if (!$Service) {

    throw "SQL Server service not created."

}

Write-Host ""
Write-Host "====================================="
Write-Host "INSTALLATION SUCCESSFUL"
Write-Host "====================================="
Write-Host ""

Write-Host "Service Name : $($Service.Name)"
Write-Host "Status       : $($Service.Status)"
Write-Host "Start Type   : $($Service.StartType)"

exit 0
