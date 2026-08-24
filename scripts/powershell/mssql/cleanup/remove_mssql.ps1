$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Mssql-CleanupSafety.ps1"

$context = Get-MssqlCleanupContext
$cleanupMode = $env:CLEANUP_MODE
if ([string]::IsNullOrWhiteSpace($cleanupMode)) { $cleanupMode = 'PRESERVE_DATA' }
$cleanupMode = $cleanupMode.Trim().ToUpperInvariant()
if ($cleanupMode -notin @('PRESERVE_DATA', 'DELETE_DATA')) { throw "Invalid CLEANUP_MODE: $cleanupMode" }
Write-Host "MSSQL cleanup mode: $cleanupMode"
if (-not (Test-MssqlProjectManaged $context)) {
    Write-Host "No verified project-managed MSSQL deployment was found. Skipping service and deployment removal."
    exit 0
}
$service = Get-Service -Name $context.ServiceName -ErrorAction SilentlyContinue
if ($service) {
    if ($service.Status -ne 'Stopped') { throw "Refusing to remove a running project-managed MSSQL service." }
    & sc.exe delete $context.ServiceName | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "Could not remove project-managed MSSQL service: $($context.ServiceName)" }
}
Remove-MssqlProjectPath -Path $context.InstallDir -Context $context
Remove-MssqlProjectPath -Path (Join-Path $context.ProjectRoot 'databases\mssql\ConfigurationFile.ini') -Context $context
if ($cleanupMode -eq 'DELETE_DATA') {
    Remove-MssqlProjectPath -Path $context.DataDir -Context $context
    Remove-MssqlProjectPath -Path $context.Marker -Context $context
    Write-Host 'Project-managed MSSQL deployment and data were removed.'
} else {
    Write-Host 'Project-managed MSSQL deployment was removed; project data was preserved.'
}
