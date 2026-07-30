$ErrorActionPreference = "Stop"

$ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

$liquibaseDir = "$ROOT\liquibase\mssql"
$masterXml = "$liquibaseDir\master.xml"

$cleanupMode = $env:CLEANUP_MODE

if ([string]::IsNullOrWhiteSpace($cleanupMode)) {
    $cleanupMode = "PRESERVE_DATA"
}

$cleanupMode = $cleanupMode.ToUpper()

Write-Host ""
Write-Host "====================================="
Write-Host "MSSQL LIQUIBASE XML CLEANUP"
Write-Host "====================================="
Write-Host ""

Write-Host "Cleanup Mode   : $cleanupMode"
Write-Host "Liquibase Path : $liquibaseDir"
Write-Host ""

if ($cleanupMode -notin @("PRESERVE_DATA", "DELETE_DATA")) {
    throw "Invalid CLEANUP_MODE: $cleanupMode"
}

if (!(Test-Path $liquibaseDir)) {
    throw "MSSQL Liquibase directory not found: $liquibaseDir"
}

# =====================================
# PRESERVE DATA MODE
# =====================================

if ($cleanupMode -eq "PRESERVE_DATA") {

    Write-Host "MSSQL data is being preserved."
    Write-Host "Generated Liquibase XML files will also be preserved."
    Write-Host ""

    Write-Host "====================================="
    Write-Host "MSSQL LIQUIBASE XML PRESERVED"
    Write-Host "====================================="
    Write-Host ""

    exit 0
}

# =====================================
# FIND GENERATED XML FILES
# =====================================

Write-Host "Finding generated Liquibase XML files..."
Write-Host ""

$generatedXmlFiles = Get-ChildItem `
    -Path $liquibaseDir `
    -Filter "*.xml" `
    -File |
    Where-Object {
        $_.Name -ne "master.xml"
    }

# =====================================
# REMOVE GENERATED XML FILES
# =====================================

if ($generatedXmlFiles.Count -eq 0) {

    Write-Host "No generated Liquibase XML files found."
}
else {

    foreach ($xmlFile in $generatedXmlFiles) {

        Write-Host "Removing: $($xmlFile.Name)"

        Remove-Item `
            -Path $xmlFile.FullName `
            -Force
    }
}

# =====================================
# RESET MASTER.XML
# =====================================

Write-Host ""
Write-Host "Resetting master.xml..."
Write-Host ""

$masterContent = @'
<?xml version="1.0" encoding="UTF-8"?>

<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog https://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

</databaseChangeLog>
'@

Set-Content `
    -Path $masterXml `
    -Value $masterContent `
    -Encoding UTF8

# =====================================
# VALIDATION
# =====================================

Write-Host "Validating MSSQL Liquibase XML cleanup..."
Write-Host ""

$remainingXmlFiles = Get-ChildItem `
    -Path $liquibaseDir `
    -Filter "*.xml" `
    -File |
    Where-Object {
        $_.Name -ne "master.xml"
    }

if ($remainingXmlFiles.Count -gt 0) {
    throw "Generated MSSQL Liquibase XML files still exist."
}

if (!(Test-Path $masterXml)) {
    throw "master.xml not found after reset."
}

Write-Host "Generated Liquibase XML files removed successfully."
Write-Host "master.xml reset successfully."

Write-Host ""
Write-Host "====================================="
Write-Host "MSSQL LIQUIBASE XML CLEANUP SUCCESSFUL"
Write-Host "====================================="
Write-Host ""

exit 0