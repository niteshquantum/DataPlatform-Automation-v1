$ErrorActionPreference = "Stop"

function Write-Log {
    param([string]$Message)

    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

Write-Log "Searching PostgreSQL service"

$Service = Get-Service |
Where-Object {
    $_.Name -match "postgres"
} |
Select-Object -First 1

if ($Service) {

    if ($Service.Status -eq "Running") {

        Write-Log "Stopping PostgreSQL service"

        Stop-Service `
            -Name $Service.Name `
            -Force

        Start-Sleep 5
    }
}

$Psql = Get-Command psql -ErrorAction SilentlyContinue

if (!$Psql) {

    Write-Log "PostgreSQL already removed"

    exit 0
}

$InstallRoot = Split-Path `
    (Split-Path $Psql.Source)

Write-Log "Detected installation path"

Write-Log $InstallRoot

try {

    Remove-Item `
        -Path $InstallRoot `
        -Recurse `
        -Force

    Write-Log "Installation removed"
}
catch {

    Write-Log "Manual cleanup may be required"
}

Write-Log "PostgreSQL removal process completed"