$ErrorActionPreference = 'Stop'

function Get-MongoDBCleanupContext {
    $projectRoot = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
    . "$projectRoot\scripts\powershell\common\load_config.ps1"
    $config = Load-Config "$projectRoot\config\windows\mongodb.conf"
    foreach ($key in @('MONGODB_HOST', 'MONGODB_PORT', 'MONGODB_DATABASE', 'MONGODB_SERVICE_NAME', 'MONGODB_INSTALL_DIR', 'MONGODB_DATA_DIR')) {
        if ([string]::IsNullOrWhiteSpace($config[$key])) { throw "$key is missing in config/windows/mongodb.conf" }
    }
    function Resolve-ManagedPath([string]$relativePath) {
        $path = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $relativePath))
        $prefix = $projectRoot.TrimEnd('\') + '\'
        if (-not $path.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Configured MongoDB path must be inside PROJECT_ROOT: $relativePath" }
        return $path
    }
    $installDir = Resolve-ManagedPath $config['MONGODB_INSTALL_DIR']
    return [pscustomobject]@{
        ProjectRoot = $projectRoot; Config = $config; ServiceName = $config['MONGODB_SERVICE_NAME']
        InstallDir = $installDir; DataDir = Resolve-ManagedPath $config['MONGODB_DATA_DIR']
        MongodExe = Join-Path $installDir 'server\bin\mongod.exe'; MongoshExe = Join-Path $installDir 'mongosh\bin\mongosh.exe'
        Marker = Join-Path $installDir '.project-managed-mongodb'
    }
}

function Test-MongoDBProjectManaged([object]$Context) {
    if (-not (Test-Path -LiteralPath $Context.Marker)) { return $false }
    $marker = Get-Content -LiteralPath $Context.Marker -Raw -ErrorAction Stop
    foreach ($entry in @("service_name=$($Context.ServiceName)", "install_dir=$($Context.Config['MONGODB_INSTALL_DIR'])", "data_dir=$($Context.Config['MONGODB_DATA_DIR'])")) {
        if ($marker -notmatch "(?im)^$([regex]::Escape($entry))$") { return $false }
    }
    $service = Get-CimInstance Win32_Service -Filter "Name='$($Context.ServiceName.Replace("'", "''"))'" -ErrorAction SilentlyContinue
    if (-not $service) { return $true }
    return $service.PathName.IndexOf($Context.MongodExe, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
}

function New-MongoDBOwnershipMarker {
    $context = Get-MongoDBCleanupContext
    $service = Get-CimInstance Win32_Service -Filter "Name='$($context.ServiceName.Replace("'", "''"))'" -ErrorAction Stop
    if (-not $service -or $service.PathName.IndexOf($context.MongodExe, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) { throw 'Cannot mark MongoDB ownership because the service is not project-managed.' }
    @("service_name=$($context.ServiceName)", "install_dir=$($context.Config['MONGODB_INSTALL_DIR'])", "data_dir=$($context.Config['MONGODB_DATA_DIR'])") | Set-Content -LiteralPath $context.Marker -Encoding UTF8
    Write-Host "MongoDB project ownership marker created: $($context.Marker)"
}

function Remove-MongoDBProjectPath([string]$Path, [object]$Context) {
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $prefix = $Context.ProjectRoot.TrimEnd('\') + '\'
    if (-not $fullPath.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) { throw "Refusing to delete a path outside PROJECT_ROOT: $fullPath" }
    if (Test-Path -LiteralPath $fullPath) { Remove-Item -LiteralPath $fullPath -Recurse -Force -ErrorAction Stop }
}
