$ErrorActionPreference = "Stop"

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

# =====================================
# LOAD CONFIG
# =====================================

. "$PROJECT_ROOT\scripts\powershell\common\load_config.ps1"

$CONFIG_FILE = "$PROJECT_ROOT\config\common\tools.conf"

if (!(Test-Path $CONFIG_FILE)) {
    Write-Error "Config file not found: $CONFIG_FILE"
    exit 1
}

$Config = Load-Config $CONFIG_FILE

$SevenZipUrl = $Config["SEVENZIP_URL"]
$InstallPath = $Config["SEVENZIP_INSTALL_PATH"]

# =====================================
# CHECK EXISTING INSTALLATION
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "CHECKING 7-ZIP"
Write-Host "====================================="
Write-Host ""

if (Test-Path $InstallPath) {
    Write-Host "[SUCCESS] 7-Zip is available."
    exit 0
}

# =====================================
# DOWNLOAD INSTALLER
# =====================================

$Installer = Join-Path $env:TEMP "7zip-installer.exe"

Write-Host "[INFO] 7-Zip not found."
Write-Host "[INFO] Downloading 7-Zip..."

Invoke-WebRequest `
    -Uri $SevenZipUrl `
    -OutFile $Installer `
    -UseBasicParsing

# =====================================
# INSTALL
# =====================================

Write-Host "[INFO] Installing 7-Zip..."

Start-Process `
    -FilePath $Installer `
    -ArgumentList "/S" `
    -Wait

# =====================================
# VERIFY INSTALLATION
# =====================================

if (!(Test-Path $InstallPath)) {
    Write-Error "7-Zip installation failed."
    exit 1
}

Remove-Item $Installer -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "====================================="
Write-Host "7-ZIP READY"
Write-Host "====================================="
Write-Host "Path : $InstallPath"
Write-Host "====================================="

exit 0