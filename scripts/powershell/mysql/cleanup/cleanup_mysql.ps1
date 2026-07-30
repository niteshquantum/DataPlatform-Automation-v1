$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$stopScript        = "$PSScriptRoot\stop_mysql.ps1"
$dataCleanupScript = "$PSScriptRoot\cleanup_mysql_data.ps1"
$deploymentScript  = "$PSScriptRoot\remove_mysql_deployment.ps1"
$stateResetScript  = "$PSScriptRoot\reset_mysql_terraform_state.ps1"
$validationScript  = "$PSScriptRoot\validate_cleanup.ps1"
$xmlCleanupScript = "$PSScriptRoot\cleanup_mysql_xml.ps1"
$loadArtifactsCleanupScript = "$PSScriptRoot\cleanup_mysql_load_artifacts.ps1"

Write-Host ""
Write-Host "====================================="
Write-Host "MYSQL CLEANUP AUTOMATION"
Write-Host "====================================="
Write-Host ""

# =====================================
# READ CLEANUP MODE
# =====================================

$cleanupMode = $env:CLEANUP_MODE

if ([string]::IsNullOrWhiteSpace($cleanupMode)) {
    $cleanupMode = "PRESERVE_DATA"
}

$cleanupMode = $cleanupMode.ToUpper()

Write-Host "Project Root : $ROOT"
Write-Host "Cleanup Mode : $cleanupMode"
Write-Host ""

# =====================================
# VALIDATE CLEANUP MODE
# =====================================

if ($cleanupMode -notin @("PRESERVE_DATA", "DELETE_DATA")) {
    throw "Invalid CLEANUP_MODE: $cleanupMode. Allowed values: PRESERVE_DATA or DELETE_DATA"
}

# =====================================
# VALIDATE CLEANUP SCRIPTS
# =====================================

$requiredScripts = @(
    $stopScript,
    $dataCleanupScript,
    $deploymentScript,
    $stateResetScript,
    $validationScript,
    $xmlCleanupScript,
    $loadArtifactsCleanupScript
)

foreach ($script in $requiredScripts) {

    if (!(Test-Path $script)) {
        throw "Required cleanup script not found: $script"
    }
}

# =====================================
# STEP 1 - STOP MYSQL
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "STEP 1 - STOP MYSQL"
Write-Host "====================================="
Write-Host ""

& $stopScript

if ($LASTEXITCODE -ne 0) {
    throw "MySQL stop failed"
}

# =====================================
# STEP 2 - CLEANUP MYSQL DATA
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "STEP 2 - CLEANUP MYSQL DATA"
Write-Host "====================================="
Write-Host ""

& $dataCleanupScript

if ($LASTEXITCODE -ne 0) {
    throw "MySQL data cleanup failed"
}

# =====================================
# STEP 3 - REMOVE MYSQL DEPLOYMENT
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "STEP 3 - REMOVE MYSQL DEPLOYMENT"
Write-Host "====================================="
Write-Host ""

& $deploymentScript

if ($LASTEXITCODE -ne 0) {
    throw "MySQL deployment removal failed"
}

# =====================================
# STEP 4 - RESET TERRAFORM STATE
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "STEP 4 - RESET MYSQL TERRAFORM STATE"
Write-Host "====================================="
Write-Host ""

& $stateResetScript

if ($LASTEXITCODE -ne 0) {
    throw "MySQL Terraform state reset failed"
}

# =====================================
# STEP 5 - CLEANUP LIQUIBASE XML
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "STEP 5 - CLEANUP LIQUIBASE XML"
Write-Host "====================================="
Write-Host ""

& $xmlCleanupScript

if ($LASTEXITCODE -ne 0) {
    throw "MySQL Liquibase XML cleanup failed"
}

# =====================================
# STEP 6 - CLEANUP LOAD ARTIFACTS
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "STEP 6 - CLEANUP LOAD ARTIFACTS"
Write-Host "====================================="
Write-Host ""

& $loadArtifactsCleanupScript

if ($LASTEXITCODE -ne 0) {
    throw "MySQL load artifacts cleanup failed"
}
# =====================================
# STEP 7 - VALIDATE CLEANUP
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "STEP 7 - VALIDATE MYSQL CLEANUP"
Write-Host "====================================="
Write-Host ""

& $validationScript

if ($LASTEXITCODE -ne 0) {
    throw "MySQL cleanup validation failed"
}

# =====================================
# SUCCESS
# =====================================

Write-Host ""
Write-Host "====================================="
Write-Host "MYSQL CLEANUP AUTOMATION SUCCESSFUL"
Write-Host "====================================="
Write-Host ""

Write-Host "Cleanup Mode : $cleanupMode"

if ($cleanupMode -eq "PRESERVE_DATA") {
    Write-Host "MySQL Data   : PRESERVED"
}
else {
    Write-Host "MySQL Data   : DELETED"
}

Write-Host ""

exit 0