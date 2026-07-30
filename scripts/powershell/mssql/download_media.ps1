$ErrorActionPreference = "Stop"

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

Write-Host ""
Write-Host "====================================="
Write-Host "DOWNLOADING MSSQL INSTALLATION MEDIA"
Write-Host "====================================="
Write-Host ""

# =====================================
# DOWNLOAD MEDIA
# =====================================

python "$PROJECT_ROOT\scripts\python\mssql\setup\download_media.py"

if ($LASTEXITCODE -ne 0) {
    throw "MSSQL media download failed."
}

# =====================================
# EXTRACT MEDIA
# =====================================

python "$PROJECT_ROOT\scripts\python\mssql\setup\extract_media.py"

if ($LASTEXITCODE -ne 0) {
    throw "MSSQL media extraction failed."
}

Write-Host ""
Write-Host "====================================="
Write-Host "MSSQL INSTALLATION MEDIA READY"
Write-Host "====================================="
Write-Host ""