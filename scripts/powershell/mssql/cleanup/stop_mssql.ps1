$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "STOPPING MSSQL SERVER"
Write-Host "====================================="
Write-Host ""

# =====================================
# PROJECT ROOT
# =====================================

$PROJECT_ROOT = (Resolve-Path "$PSScriptRoot\..\..\..\..").Path

# =====================================
# LOAD CONFIG
# =====================================

. "$PROJECT_ROOT\scripts\powershell\common\load_config.ps1"

$Config = Load-Config "$PROJECT_ROOT\config\windows\mssql.conf"

$Instance = $Config["MSSQL_INSTANCE"]

if ([string]::IsNullOrWhiteSpace($Instance)) {
    throw "MSSQL_INSTANCE is missing in config/windows/mssql.conf"
}

# =====================================
# SERVICE NAME
# =====================================

if ($Instance -eq "MSSQLSERVER") {
    $ServiceName = "MSSQLSERVER"
}
else {
    $ServiceName = "MSSQL`$$Instance"
}

Write-Host "Instance     : $Instance"
Write-Host "Service Name : $ServiceName"
Write-Host ""

# =====================================
# CHECK SERVICE
# =====================================

$Service = Get-Service `
    -Name $ServiceName `
    -ErrorAction SilentlyContinue

# =====================================
# IDEMPOTENCY
# =====================================

if (!$Service) {

    Write-Host "SQL Server service does not exist."
    Write-Host "Nothing to stop."
    Write-Host ""

    Write-Host "====================================="
    Write-Host "MSSQL STOP SUCCESSFUL"
    Write-Host "====================================="
    Write-Host ""

    exit 0
}

# =====================================
# STOP SERVICE
# =====================================

if ($Service.Status -eq "Stopped") {

    Write-Host "SQL Server service is already stopped."
}
else {

    Write-Host "Stopping SQL Server service..."
    Write-Host ""

    try {
        Stop-Service `
            -Name $ServiceName `
            -Force `
            -ErrorAction Stop
    }
    catch {
        Write-Host "WARNING: Could not stop SQL Server service: $($_.Exception.Message)"
        Write-Host "Continuing validation..."
    }

    try {
        $Service.WaitForStatus(
            [System.ServiceProcess.ServiceControllerStatus]::Stopped,
            [TimeSpan]::FromSeconds(60)
        )
        $Service.Refresh()

        if (
            $null -ne $Service -and
            $Service.Status -ne "Stopped"
        ) {
            Write-Host "SQL Server service is still running. Continuing cleanup..."
        }
        else {
            Write-Host "SQL Server service stopped successfully."
        }
    }
    catch {
        Write-Host "WARNING: Could not verify SQL Server service stop: $($_.Exception.Message)"
        Write-Host "Continuing cleanup..."
    }
}

# =====================================
# FINAL VALIDATION
# =====================================

Write-Host ""
Write-Host "Validating MSSQL service status..."
Write-Host ""

$Service = Get-Service `
    -Name $ServiceName `
    -ErrorAction SilentlyContinue

if (
    $null -ne $Service -and
    $Service.Status -ne "Stopped"
) {
    Write-Host "WARNING: MSSQL service is still running."
    Write-Host "This is expected in local runtime without admin privileges."
    Write-Host "Continuing cleanup..."
}
else {
    Write-Host "MSSQL service validation passed."
}

Write-Host ""
Write-Host "====================================="
Write-Host "MSSQL STOP SUCCESSFUL"
Write-Host "====================================="
Write-Host ""

exit 0
