$ErrorActionPreference = "Stop"

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..").Path

Write-Host ""
Write-Host "====================================="
Write-Host "DOWNLOADING DATASET"
Write-Host "====================================="
Write-Host ""

# =====================================
# DOWNLOAD DATASET
# =====================================

python "$PROJECT_ROOT\scripts\python\common\download_dataset.py"

if ($LASTEXITCODE -ne 0) {
    throw "Dataset download failed."
}

# =====================================
# EXTRACT DATASET
# =====================================

python "$PROJECT_ROOT\scripts\python\common\extract_dataset.py"

if ($LASTEXITCODE -ne 0) {
    throw "Dataset extraction failed."
}

Write-Host ""
Write-Host "====================================="
Write-Host "DATASET READY"
Write-Host "====================================="
Write-Host ""