$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$terraformExe = "$ROOT\tools\terraform\terraform.exe"
$terraformDir = "$ROOT\terraform\mysql"

Write-Host ""
Write-Host "====================================="
Write-Host "RESETTING MYSQL TERRAFORM STATE"
Write-Host "====================================="
Write-Host ""

# =====================================
# VALIDATE TERRAFORM
# =====================================

if (!(Test-Path $terraformExe)) {
    throw "Terraform executable not found: $terraformExe"
}

if (!(Test-Path $terraformDir)) {
    throw "MySQL Terraform directory not found: $terraformDir"
}

Write-Host "Terraform Path      : $terraformExe"
Write-Host "Terraform Directory : $terraformDir"
Write-Host ""

# =====================================
# MYSQL WINDOWS TERRAFORM RESOURCES
# =====================================

$mysqlResources = @(
    "null_resource.create_mysql_user_windows",
    "null_resource.start_mysql_windows",
    "null_resource.init_mysql_windows",
    "null_resource.extract_mysql_windows",
    "null_resource.download_mysql_windows"
)

Push-Location $terraformDir

try {

    # =====================================
    # READ CURRENT TERRAFORM STATE
    # =====================================

    Write-Host "Reading current Terraform state..."
    Write-Host ""

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $stateListOutput = & $terraformExe state list 2>&1
    $stateListExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference

    if ($stateListExitCode -ne 0) {
        $outputString = $stateListOutput | Out-String
        if ($outputString -match "No state file was found") {
            Write-Host "No Terraform state file found. Nothing to reset."
            exit 0
        }
        throw "Failed to read Terraform state"
    }

    $currentState = $stateListOutput

    # =====================================
    # FIND MYSQL WINDOWS RESOURCES
    # =====================================

    $resourcesToRemove = @(
        $mysqlResources |
        Where-Object {
            $currentState -contains $_
        }
    )

    if ($resourcesToRemove.Count -eq 0) {

        Write-Host "No MySQL Windows resources found in Terraform state."
        Write-Host "Nothing to reset."
    }
    else {

        Write-Host "MySQL Windows resources found:"
        Write-Host ""

        foreach ($resource in $resourcesToRemove) {
            Write-Host "  $resource"
        }

        # =====================================
        # REMOVE RESOURCES IN SINGLE OPERATION
        # =====================================

        Write-Host ""
        Write-Host "Removing MySQL Windows resources from Terraform state..."
        Write-Host ""

        & $terraformExe state rm @resourcesToRemove

        if ($LASTEXITCODE -ne 0) {
            throw "Failed to reset MySQL Terraform state"
        }
    }

    # =====================================
    # VALIDATE TERRAFORM STATE
    # =====================================

    Write-Host ""
    Write-Host "Validating Terraform state cleanup..."
    Write-Host ""

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $remainingStateOutput = & $terraformExe state list 2>&1
    $remainingStateExitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference

    if ($remainingStateExitCode -ne 0) {
        $outputString = $remainingStateOutput | Out-String
        if ($outputString -match "No state file was found") {
            Write-Host "No Terraform state file found after cleanup."
            exit 0
        }
        throw "Failed to validate Terraform state"
    }

    $remainingState = $remainingStateOutput

    $remainingMysqlResources = @(
        $mysqlResources |
        Where-Object {
            $remainingState -contains $_
        }
    )

    if ($remainingMysqlResources.Count -gt 0) {

        Write-Host "Resources still present:"
        Write-Host ""

        foreach ($resource in $remainingMysqlResources) {
            Write-Host "  $resource"
        }

        throw "MySQL Windows resources still exist in Terraform state"
    }
}
finally {

    Pop-Location
}

Write-Host ""
Write-Host "====================================="
Write-Host "MYSQL TERRAFORM STATE RESET SUCCESSFUL"
Write-Host "====================================="
Write-Host ""

exit 0