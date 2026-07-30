$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "RESETTING MONGODB TERRAFORM STATE"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$TerraformDir = Join-Path $PROJECT_ROOT "terraform\mongodb"

# =====================================
# DISPLAY CONFIGURATION
# =====================================

Write-Host "Project Root  : $PROJECT_ROOT"
Write-Host "Terraform Dir : $TerraformDir"
Write-Host ""

# =====================================
# VALIDATE TERRAFORM DIRECTORY
# =====================================

if (!(Test-Path -LiteralPath $TerraformDir)) {
    throw "MongoDB Terraform directory not found: $TerraformDir"
}

# =====================================
# SAFETY VALIDATION
# =====================================

$ExpectedTerraformDir = [System.IO.Path]::GetFullPath(
    (Join-Path $PROJECT_ROOT "terraform\mongodb")
)

$ActualTerraformDir = [System.IO.Path]::GetFullPath(
    $TerraformDir
)

if (
    -not $ActualTerraformDir.Equals(
        $ExpectedTerraformDir,
        [System.StringComparison]::OrdinalIgnoreCase
    )
) {
    throw "Terraform cleanup safety validation failed."
}

# =====================================
# HELPER FUNCTION
# =====================================

function Remove-TerraformRuntimePath {

    param (
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    if (Test-Path -LiteralPath $Path) {

        Write-Host "Removing $Description..."
        Write-Host "Path : $Path"

        Remove-Item `
            -LiteralPath $Path `
            -Recurse `
            -Force `
            -ErrorAction Stop

        if (Test-Path -LiteralPath $Path) {
            throw "Failed to remove ${Description}: $Path"
        }

        Write-Host "$Description removed successfully."
    }
    else {
        Write-Host "$Description already absent. Skipping."
    }

    Write-Host ""
}

# =====================================
# TERRAFORM RUNTIME PATHS
# =====================================

$TerraformWorkingDir = Join-Path $TerraformDir ".terraform"
$TerraformState = Join-Path $TerraformDir "terraform.tfstate"
$TerraformStateBackup = Join-Path $TerraformDir "terraform.tfstate.backup"

# =====================================
# REMOVE TERRAFORM RUNTIME STATE
# =====================================

Remove-TerraformRuntimePath `
    -Path $TerraformWorkingDir `
    -Description "Terraform working directory"

Remove-TerraformRuntimePath `
    -Path $TerraformState `
    -Description "Terraform state file"

Remove-TerraformRuntimePath `
    -Path $TerraformStateBackup `
    -Description "Terraform state backup"

# =====================================
# FINAL VALIDATION
# =====================================

Write-Host "Validating Terraform runtime state reset..."
Write-Host ""

$RemainingPaths = @()

foreach (
    $Path in @(
        $TerraformWorkingDir,
        $TerraformState,
        $TerraformStateBackup
    )
) {

    if (Test-Path -LiteralPath $Path) {
        $RemainingPaths += $Path
    }
}

if ($RemainingPaths.Count -gt 0) {

    Write-Host "Remaining Terraform runtime paths:"

    foreach ($Path in $RemainingPaths) {
        Write-Host " - $Path"
    }

    throw "MongoDB Terraform runtime state reset failed."
}

Write-Host ""
Write-Host "====================================="
Write-Host "MONGODB TERRAFORM STATE RESET COMPLETE"
Write-Host "====================================="
Write-Host ""

exit 0
