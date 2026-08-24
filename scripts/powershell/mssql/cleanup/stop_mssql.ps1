$ErrorActionPreference = "Stop"
. "$PSScriptRoot\Mssql-CleanupSafety.ps1"

$context = Get-MssqlCleanupContext
Write-Host "Stopping project-managed MSSQL service: $($context.ServiceName)"
if (-not (Test-MssqlProjectManaged $context)) {
    Write-Host "No verified project-managed MSSQL service was found. External SQL Server services are untouched."
    exit 0
}
$service = Get-Service -Name $context.ServiceName -ErrorAction SilentlyContinue
if (-not $service) { Write-Host "Project-managed MSSQL service is already absent."; exit 0 }
if ($service.Status -ne 'Stopped') {
    Stop-Service -Name $context.ServiceName -Force -ErrorAction Stop
    $service.WaitForStatus([System.ServiceProcess.ServiceControllerStatus]::Stopped, [TimeSpan]::FromSeconds(60))
}
$service.Refresh()
if ($service.Status -ne 'Stopped') { throw "Project-managed MSSQL service did not stop: $($context.ServiceName)" }
Write-Host "Project-managed MSSQL service stopped."
