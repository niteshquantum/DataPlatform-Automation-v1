$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "STARTING AND VERIFYING MSSQL SERVER"
Write-Host "====================================="
Write-Host ""

& "$PSScriptRoot\ensure_mssql_ready.ps1" -StartIfStopped

Write-Host "[SUCCESS] MSSQL Server is accepting authenticated connections."
