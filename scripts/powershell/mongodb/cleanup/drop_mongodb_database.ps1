$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\MongoDB-CleanupSafety.ps1"
if ($env:CLEANUP_MODE -ne 'DELETE_DATA') { exit 0 }
$context = Get-MongoDBCleanupContext
if (-not (Test-MongoDBProjectManaged $context)) { Write-Host 'No verified project-managed MongoDB deployment was found. External MongoDB resources are untouched.'; exit 0 }
if (-not (Test-Path -LiteralPath $context.MongoshExe)) { throw "Project-managed mongosh executable not found: $($context.MongoshExe)" }
$databaseJson = $context.Config['MONGODB_DATABASE'] | ConvertTo-Json -Compress
& $context.MongoshExe --host $context.Config['MONGODB_HOST'] --port $context.Config['MONGODB_PORT'] --quiet --eval "db.getSiblingDB($databaseJson).dropDatabase();" 
if ($LASTEXITCODE -ne 0) { throw "Failed to drop configured project MongoDB database: $($context.Config['MONGODB_DATABASE'])" }
Write-Host "Configured project MongoDB database removed: $($context.Config['MONGODB_DATABASE'])"
