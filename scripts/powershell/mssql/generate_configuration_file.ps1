$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "GENERATING MSSQL CONFIGURATION FILE"
Write-Host "====================================="
Write-Host ""

# ------------------------------------------------------------------
# Project Root
# ------------------------------------------------------------------

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..\..")

# ------------------------------------------------------------------
# Load Configuration
# ------------------------------------------------------------------

. "$ProjectRoot\scripts\powershell\common\load_config.ps1"

$config = Load-Config "$ProjectRoot\config\windows\mssql.conf"

# ------------------------------------------------------------------
# Validate Required Configuration
# ------------------------------------------------------------------

$requiredKeys = @(
    "MSSQL_INSTANCE",
    "MSSQL_PASSWORD",
    "MSSQL_FEATURES",
    "MSSQL_SECURITY_MODE",
    "MSSQL_ACCEPT_EULA",
    "MSSQL_INSTALL_UPDATES",
    "MSSQL_TCP_ENABLED",
    "MSSQL_NP_ENABLED",
    "MSSQL_SQLSVC_STARTUP",
    "MSSQL_AGTSVC_STARTUP",
    "MSSQL_BROWSER_STARTUP",
    "MSSQL_SYSADMIN_ACCOUNTS"
)

foreach ($key in $requiredKeys) {

    if (-not $config.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($config[$key])) {
        throw "Missing required configuration: $key"
    }

}

Write-Host "[OK] Configuration validation passed."

# ------------------------------------------------------------------
# Template Path
# ------------------------------------------------------------------

$templateFile = Join-Path $ProjectRoot "databases\mssql\templates\ConfigurationFile.template.ini"

if (!(Test-Path $templateFile)) {
    throw "Template file not found:`n$templateFile"
}

# ------------------------------------------------------------------
# Output Path
# ------------------------------------------------------------------

$outputFile = Join-Path $ProjectRoot "databases\mssql\ConfigurationFile.ini"

# ------------------------------------------------------------------
# Read Template
# ------------------------------------------------------------------

$content = Get-Content $templateFile -Raw

# ------------------------------------------------------------------
# Replace Placeholders
# ------------------------------------------------------------------

$replacements = @{
    "{{INSTANCE_NAME}}"           = $config["MSSQL_INSTANCE"]
    "{{SA_PASSWORD}}"             = $config["MSSQL_PASSWORD"]
    "{{FEATURES}}"                = $config["MSSQL_FEATURES"]
    "{{SECURITY_MODE}}"           = $config["MSSQL_SECURITY_MODE"]
    "{{ACCEPT_EULA}}"             = $config["MSSQL_ACCEPT_EULA"]
    "{{UPDATE_ENABLED}}"          = $config["MSSQL_INSTALL_UPDATES"]
    "{{TCP_ENABLED}}"             = $(if ($config["MSSQL_TCP_ENABLED"] -eq "True") { "1" } else { "0" })
    "{{NP_ENABLED}}"              = $(if ($config["MSSQL_NP_ENABLED"] -eq "True") { "1" } else { "0" })
    "{{SQL_SERVICE_STARTUP}}"     = $config["MSSQL_SQLSVC_STARTUP"]
    "{{AGENT_SERVICE_STARTUP}}"   = $config["MSSQL_AGTSVC_STARTUP"]
    "{{BROWSER_SERVICE_STARTUP}}" = $config["MSSQL_BROWSER_STARTUP"]
    "{{SYSADMIN_ACCOUNTS}}"       = $config["MSSQL_SYSADMIN_ACCOUNTS"]
}

foreach ($item in $replacements.GetEnumerator()) {
    $content = $content.Replace($item.Key, $item.Value)
}

# ------------------------------------------------------------------
# Save Configuration File
# ------------------------------------------------------------------

$content | Set-Content -Path $outputFile -Encoding UTF8

Write-Host ""
Write-Host "[OK] Configuration file generated successfully."
Write-Host ""
Write-Host "Location:"
Write-Host $outputFile
Write-Host ""