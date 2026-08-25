$ErrorActionPreference = "Stop"

function Get-MssqlCleanupContext {
    $projectRoot = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path
    . "$projectRoot\scripts\powershell\common\load_config.ps1"
    $config = Load-Config "$projectRoot\config\windows\mssql.conf"

    foreach ($key in @("MSSQL_INSTANCE", "MSSQL_DB", "MSSQL_INSTALL_DIR", "MSSQL_DATA_DIR")) {
        if ([string]::IsNullOrWhiteSpace($config[$key])) {
            throw "$key is missing in config/windows/mssql.conf"
        }
    }

    function Resolve-ManagedPath([string]$relativePath) {
        $path = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $relativePath))
        $rootPrefix = $projectRoot.TrimEnd('\') + '\'
        if (-not $path.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
            throw "Configured MSSQL path must be inside PROJECT_ROOT: $relativePath"
        }
        return $path
    }

    $serviceName = if ($config["MSSQL_INSTANCE"] -eq "MSSQLSERVER") { "MSSQLSERVER" } else { "MSSQL`$$($config['MSSQL_INSTANCE'])" }
    return [pscustomobject]@{
        ProjectRoot = $projectRoot
        Config = $config
        ServiceName = $serviceName
        InstallDir = Resolve-ManagedPath $config["MSSQL_INSTALL_DIR"]
        DataDir = Resolve-ManagedPath $config["MSSQL_DATA_DIR"]
        Marker = Join-Path $projectRoot "databases\mssql\.project-managed-mssql"
    }
}

function Test-MssqlProjectManaged([object]$Context) {
    if (-not (Test-Path -LiteralPath $Context.Marker)) { return $false }
    $marker = Get-Content -LiteralPath $Context.Marker -Raw -ErrorAction Stop
    if ($marker -notmatch "(?im)^instance=$([regex]::Escape($Context.Config['MSSQL_INSTANCE']))$") { return $false }

    foreach ($entry in @(
        "install_dir=$($Context.Config['MSSQL_INSTALL_DIR'])",
        "data_dir=$($Context.Config['MSSQL_DATA_DIR'])"
    )) {
        if ($marker -notmatch "(?im)^$([regex]::Escape($entry))$") { return $false }
    }

    $service = Get-CimInstance Win32_Service -Filter "Name='$($Context.ServiceName.Replace("'", "''"))'" -ErrorAction SilentlyContinue
    if (-not $service) { return $true }
    return $service.PathName.IndexOf($Context.InstallDir, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
}

function Remove-MssqlProjectPath([string]$Path, [object]$Context) {
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $rootPrefix = $Context.ProjectRoot.TrimEnd('\') + '\'
    if (-not $fullPath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to delete a path outside PROJECT_ROOT: $fullPath"
    }
    if (Test-Path -LiteralPath $fullPath) {
        Remove-Item -LiteralPath $fullPath -Recurse -Force -ErrorAction Stop
    }
}
