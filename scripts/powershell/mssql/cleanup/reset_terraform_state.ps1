$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "RESETTING MSSQL TERRAFORM STATE"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$TerraformExe = Join-Path `
    $PROJECT_ROOT `
    "tools\terraform\terraform.exe"

$TerraformDir = Join-Path `
    $PROJECT_ROOT `
    "terraform\mssql"

Write-Host "Terraform Path      : $TerraformExe"
Write-Host "Terraform Directory : $TerraformDir"
Write-Host ""

# =====================================
# VALIDATE TERRAFORM
# =====================================

if (!(Test-Path -LiteralPath $TerraformExe)) {
    throw "Terraform executable not found: $TerraformExe"
}

if (!(Test-Path -LiteralPath $TerraformDir)) {
    throw "MSSQL Terraform directory not found: $TerraformDir"
}

# =====================================
# WINDOWS TERRAFORM RESOURCES
# =====================================

$WindowsResources = @(
    "null_resource.start_mssql_windows",
    "null_resource.install_mssql_windows",
    "null_resource.download_mssql_windows"
)

# =====================================
# ENTER TERRAFORM DIRECTORY
# =====================================

Push-Location $TerraformDir

try {

    # =====================================
    # CHECK TERRAFORM STATE FILE
    # =====================================

    $TerraformStateFile = Join-Path `
        $TerraformDir `
        "terraform.tfstate"

    if (!(Test-Path -LiteralPath $TerraformStateFile)) {

        Write-Host "No Terraform state file found."
        Write-Host "Nothing to reset."
        Write-Host ""

        Write-Host "====================================="
        Write-Host "MSSQL TERRAFORM STATE RESET SUCCESSFUL"
        Write-Host "====================================="
        Write-Host ""

        exit 0
    }

    # =====================================
    # READ CURRENT TERRAFORM STATE
    # =====================================

    Write-Host "Reading current Terraform state..."
    Write-Host ""

    $StateResources = @(
        & $TerraformExe state list
    )

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read MSSQL Terraform state."
    }

    # =====================================
    # HANDLE EMPTY TERRAFORM STATE
    # =====================================

    if ($StateResources.Count -eq 0) {

        Write-Host "Terraform state contains no resources."
        Write-Host "Nothing to reset."
        Write-Host ""

        Write-Host "====================================="
        Write-Host "MSSQL TERRAFORM STATE RESET SUCCESSFUL"
        Write-Host "====================================="
        Write-Host ""

        exit 0
    }

    # =====================================
    # REMOVE WINDOWS RESOURCES
    # =====================================

    $ResourcesFound = $false

    foreach ($Resource in $WindowsResources) {

        if ($StateResources -contains $Resource) {

            $ResourcesFound = $true

            Write-Host "Removing Terraform state resource:"
            Write-Host $Resource
            Write-Host ""

            & $TerraformExe state rm $Resource

            if ($LASTEXITCODE -ne 0) {
                throw "Failed to remove Terraform state resource: $Resource"
            }

            Write-Host "Terraform state resource removed successfully."
            Write-Host ""
        }
        else {

            Write-Host "Resource not found in Terraform state:"
            Write-Host $Resource
            Write-Host "Skipping."
            Write-Host ""
        }
    }

    if (-not $ResourcesFound) {

        Write-Host "No MSSQL Windows resources found in Terraform state."
        Write-Host "Nothing to reset."
        Write-Host ""
    }

    # =====================================
    # VALIDATE TERRAFORM STATE RESET
    # =====================================

    Write-Host "Validating Terraform state cleanup..."
    Write-Host ""

    $RemainingStateResources = @(
        & $TerraformExe state list
    )

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to validate MSSQL Terraform state."
    }

    foreach ($Resource in $WindowsResources) {

        if ($RemainingStateResources -contains $Resource) {
            throw "Terraform state cleanup validation failed. Resource still exists: $Resource"
        }
    }

    Write-Host "MSSQL Windows Terraform resources removed successfully."

    Write-Host ""
    Write-Host "====================================="
    Write-Host "MSSQL TERRAFORM STATE RESET SUCCESSFUL"
    Write-Host "====================================="
    Write-Host ""
}
finally {

    Pop-Location
}

exit 0