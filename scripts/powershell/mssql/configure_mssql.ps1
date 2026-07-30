#Requires -Version 5.1

<#
.SYNOPSIS
    Configures SQL Server network settings using the SQL Server WMI Provider.

.DESCRIPTION
    This script enables TCP/IP for a SQL Server instance, disables dynamic
    TCP ports, configures a static TCP port, configures SQL Browser startup,
    restarts services only when required, and validates the resulting
    configuration.

.NOTES
    Uses:
        Microsoft.SqlServer.Management.Smo.Wmi.ManagedComputer

    Does NOT:
        - Modify the Windows Registry directly.
        - Use unsupported APIs.
#>

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:ConfigurationChanged = $false



############################################################
# Project Root
############################################################

$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDirectory "..\..\..")

############################################################
# Load Configuration Loader
############################################################

$IsAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $IsAdmin) {
    throw "configure_mssql.ps1 must be run from an elevated PowerShell session (Run as Administrator)."
}

. (Join-Path $ProjectRoot "scripts\powershell\common\load_config.ps1")

############################################################
# Load MSSQL Configuration
############################################################

$configPath = Join-Path $ProjectRoot "config\windows\mssql.conf"

$config = Load-Config -ConfigFile $configPath

$InstanceName = $config["MSSQL_INSTANCE"]
$StaticPort   = $config["MSSQL_PORT"]

if ([string]::IsNullOrWhiteSpace($InstanceName)) {
    throw "MSSQL_INSTANCE is missing in mssql.conf."
}

if ([string]::IsNullOrWhiteSpace($StaticPort)) {
    throw "MSSQL_PORT is missing in mssql.conf."
}

############################################################
# Logging
############################################################

function Write-Section {
    param(
        [Parameter(Mandatory)]
        [string]$Message
    )

    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "============================================================" -ForegroundColor Cyan
}

function Write-Info {
    param(
        [Parameter(Mandatory)]
        [string]$Message
    )

    Write-Host "[INFO ] $Message" -ForegroundColor Gray
}

function Write-Success {
    param(
        [Parameter(Mandatory)]
        [string]$Message
    )

    Write-Host "[ OK  ] $Message" -ForegroundColor Green
}

function Write-WarningLog {
    param(
        [Parameter(Mandatory)]
        [string]$Message
    )

    Write-Host "[WARN ] $Message" -ForegroundColor Yellow
}

function Write-ErrorLog {
    param(
        [Parameter(Mandatory)]
        [string]$Message
    )

    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

############################################################
# SQL WMI Assembly
############################################################

function Import-SqlWmiAssembly {

    $assemblyLoaded =
        [AppDomain]::CurrentDomain.GetAssemblies() |
        Where-Object {
            $_.GetName().Name -eq "Microsoft.SqlServer.SqlWmiManagement"
        }

    if ($assemblyLoaded) {
        Write-Info "SQL WMI assembly already loaded."
        return
    }

    # ---------------------------------------------
    # Try loading from GAC (Preferred)
    # ---------------------------------------------

    $assembly = [System.Reflection.Assembly]::LoadWithPartialName(
        "Microsoft.SqlServer.SqlWmiManagement"
    )

    if ($assembly) {

        Write-Success "SQL WMI assembly loaded from GAC."

        return
    }

    # ---------------------------------------------
    # Fallback to SDK locations
    # ---------------------------------------------

    $assemblyCandidates = @(
        "C:\Program Files\Microsoft SQL Server\160\SDK\Assemblies\Microsoft.SqlServer.SqlWmiManagement.dll",
        "C:\Program Files (x86)\Microsoft SQL Server\160\SDK\Assemblies\Microsoft.SqlServer.SqlWmiManagement.dll"
    )

    foreach ($candidate in $assemblyCandidates) {

        if (Test-Path $candidate) {

            Add-Type -Path $candidate

            Write-Success "SQL WMI assembly loaded from SDK."

            return
        }
    }

    throw "Unable to load Microsoft.SqlServer.SqlWmiManagement assembly."
}

############################################################
# Managed Computer
############################################################

function Get-ManagedComputer {

    Import-SqlWmiAssembly

    Write-Info "Connecting to SQL Server WMI Provider..."

    $managedComputer =
        New-Object Microsoft.SqlServer.Management.Smo.Wmi.ManagedComputer

    Write-Success "Connected to SQL Server WMI Provider."

    return $managedComputer
}

############################################################
# Locate SQL Instance
############################################################

function Get-ServerInstance {

    param(
        [Parameter(Mandatory)]
        [Microsoft.SqlServer.Management.Smo.Wmi.ManagedComputer]
        $ManagedComputer,

        [Parameter(Mandatory)]
        [string]
        $InstanceName
    )

    Write-Info "Searching for SQL Server instance '$InstanceName'..."

    foreach ($serverInstance in $ManagedComputer.ServerInstances) {

        if ($serverInstance.Name -ieq $InstanceName) {

            Write-Success "SQL Server instance found."

            return $serverInstance
        }
    }

    throw "SQL Server instance '$InstanceName' was not found."
}

############################################################
# Locate TCP Protocol
############################################################

function Get-TcpProtocol {

    param(
        [Parameter(Mandatory)]
        $ServerInstance
    )

    foreach ($protocol in $ServerInstance.ServerProtocols) {

        if ($protocol.Name -ieq "Tcp") {

            return $protocol
        }
    }

    throw "TCP/IP protocol not found."
}
############################################################
# Locate IPAll
############################################################

function Get-IPAllAddress {

    param(
        [Parameter(Mandatory)]
        $ManagedComputer,

        [Parameter(Mandatory)]
        $TcpProtocol
    )

    $ipAll = $ManagedComputer.GetSmoObject(
        $TcpProtocol.Urn.Value + "/IPAddress[@Name='IPAll']"
    )

    if ($null -eq $ipAll) {

        throw "IPAll configuration was not found."

    }

    return $ipAll
}
############################################################
# Get Writable IP Property
############################################################

function Get-IPProperty {

    param(
        [Parameter(Mandatory)]
        $IPAddress,

        [Parameter(Mandatory)]
        [string]$PropertyName
    )

    foreach ($property in $IPAddress.IPAddressProperties) {

        if ($property.Name -ieq $PropertyName) {

            return $property
        }
    }

    throw "Property '$PropertyName' not found."
}

############################################################
# Enable TCP/IP
############################################################

function Enable-TcpProtocol {

    param(
        [Parameter(Mandatory)]
        $TcpProtocol
    )

    if ($TcpProtocol.IsEnabled) {

        Write-Info "TCP/IP protocol is already enabled."
        return
    }

    Write-Info "Enabling TCP/IP protocol..."

    $TcpProtocol.IsEnabled = $true
    $script:ConfigurationChanged = $true

    Write-Success "TCP/IP protocol enabled."
}

############################################################
# Configure Static Port
############################################################

function Set-StaticTcpPort {

    param(
        [Parameter(Mandatory)]
        $IPAddress,

        [Parameter(Mandatory)]
        [string]$Port
    )

    $dynamicPortProperty = Get-IPProperty `
        -IPAddress $IPAddress `
        -PropertyName "TcpDynamicPorts"

    $tcpPortProperty = Get-IPProperty `
        -IPAddress $IPAddress `
        -PropertyName "TcpPort"

    $needsUpdate = $false

    if ($dynamicPortProperty.Value -ne "") {

        Write-Info "Disabling Dynamic TCP Ports..."

        $dynamicPortProperty.Value = ""

        $needsUpdate = $true

        Write-Success "Dynamic TCP Ports disabled."
    }
    else {

        Write-Info "Dynamic TCP Ports already disabled."
    }

    if ($tcpPortProperty.Value -ne $Port) {

        Write-Info "Configuring static TCP port $Port..."

        $tcpPortProperty.Value = $Port

        $needsUpdate = $true

        Write-Success "Static TCP port configured."
    }
    else {

        Write-Info "Static TCP port already configured."
    }

    if ($needsUpdate) {

        $script:ConfigurationChanged = $true
    }
}

############################################################
# Persist WMI Changes
############################################################

function Save-NetworkConfiguration {

    param(
        [Parameter(Mandatory)]
        $TcpProtocol
    )

    if (-not $script:ConfigurationChanged) {

        Write-Info "No SQL Server network configuration changes detected."

        return
    }

    Write-Info "Persisting SQL Server network configuration..."

    try {

        $TcpProtocol.Alter()

    }
    catch {

        Write-Host ""
        Write-Host "=============== SMO ERROR ===============" -ForegroundColor Yellow

        $_.Exception | Format-List * -Force

        if ($_.Exception.InnerException) {

            Write-Host ""
            Write-Host "============= INNER ERROR ===============" -ForegroundColor Yellow

            $_.Exception.InnerException | Format-List * -Force

        }

        throw

    }

    Write-Success "Network configuration saved."

}

############################################################
# Configure SQL Browser
############################################################

function Set-SqlBrowserStartup {

    $browserService = Get-Service -Name "SQLBrowser" -ErrorAction SilentlyContinue

    if ($null -eq $browserService) {

        Write-WarningLog "SQL Browser service is not installed."

        return
    }

    if ($browserService.StartType -ne "Automatic") {

        Write-Info "Setting SQL Browser startup type to Automatic..."

        Set-Service `
            -Name "SQLBrowser" `
            -StartupType Automatic

        $script:ConfigurationChanged = $true

        Write-Success "SQL Browser startup type configured."
    }
    else {

        Write-Info "SQL Browser startup type already Automatic."
    }
}
############################################################
# Restart SQL Services
############################################################

function Restart-SqlServices {

    param(
        [Parameter(Mandatory)]
        [string]$InstanceName
    )

    if (-not $script:ConfigurationChanged) {

        Write-Info "Configuration unchanged. Service restart not required."

        return
    }

    $engineServiceName =
        if ($InstanceName -ieq "MSSQLSERVER") {
            "MSSQLSERVER"
        }
        else {
            "MSSQL`$$InstanceName"
        }

    Write-Info "Restarting SQL Server service '$engineServiceName'..."

    Restart-Service `
        -Name $engineServiceName `
        -Force `
        -ErrorAction Stop

    Write-Success "SQL Server service restarted."

    $browserService = Get-Service -Name "SQLBrowser" -ErrorAction SilentlyContinue

    if ($null -ne $browserService) {

        if ($browserService.Status -ne "Running") {

            Write-Info "Starting SQL Browser service..."

            Start-Service -Name "SQLBrowser"

            Write-Success "SQL Browser service started."
        }
    }
}

############################################################
# Wait For Service
############################################################

function Wait-ServiceRunning {

    param(
        [Parameter(Mandatory)]
        [string]$ServiceName,

        [int]$TimeoutSeconds = 120
    )

    Write-Info "Waiting for service '$ServiceName'..."

    $service = Get-Service -Name $ServiceName -ErrorAction Stop

    $service.WaitForStatus(
        [System.ServiceProcess.ServiceControllerStatus]::Running,
        [TimeSpan]::FromSeconds($TimeoutSeconds)
    )
    $service.Refresh()

    if ($service.Status -ne "Running") { throw "Service '$ServiceName' failed to reach Running state." }

    Write-Success "Service '$ServiceName' is running."
}

############################################################
# Verify TCP Configuration
############################################################

function Test-NetworkConfiguration {

    param(
        [Parameter(Mandatory)]
        $TcpProtocol,

        [Parameter(Mandatory)]
        [string]$ExpectedPort
    )

    $ipAll = Get-IPAllAddress `
        -ManagedComputer $managedComputer `
        -TcpProtocol $tcpProtocol

    $dynamicPort = Get-IPProperty `
        -IPAddress $ipAll `
        -PropertyName "TcpDynamicPorts"

    $staticPort = Get-IPProperty `
        -IPAddress $ipAll `
        -PropertyName "TcpPort"

    if (-not $TcpProtocol.IsEnabled) {

        throw "TCP/IP protocol is disabled."
    }

    if ($dynamicPort.Value -ne "") {

        throw "Dynamic TCP Ports are still enabled."
    }

    if ($staticPort.Value -ne $ExpectedPort) {

        throw "Static TCP Port verification failed."
    }

    Write-Success "TCP/IP configuration verified successfully."
}

############################################################
# Verify SQL Browser
############################################################

function Test-SqlBrowser {

    $browserService = Get-Service `
        -Name "SQLBrowser" `
        -ErrorAction SilentlyContinue

    if ($null -eq $browserService) {

        Write-WarningLog "SQL Browser service not installed."

        return
    }

    if ($browserService.StartType -ne "Automatic") {

        throw "SQL Browser startup type is not Automatic."
    }

    if ($browserService.Status -ne "Running") {

        throw "SQL Browser service is not running."
    }

    Write-Success "SQL Browser verified."
}

############################################################
# Main
############################################################

try {

    Write-Section "CONFIGURING SQL SERVER NETWORK"

    $managedComputer = Get-ManagedComputer

    $serverInstance = Get-ServerInstance `
        -ManagedComputer $managedComputer `
        -InstanceName $InstanceName

    $tcpProtocol = Get-TcpProtocol `
        -ServerInstance $serverInstance

    $ipAll = Get-IPAllAddress `
        -ManagedComputer $managedComputer `
        -TcpProtocol $tcpProtocol

    Enable-TcpProtocol `
        -TcpProtocol $tcpProtocol

    Set-StaticTcpPort `
        -IPAddress $ipAll `
        -Port $StaticPort

    Save-NetworkConfiguration `
        -TcpProtocol $tcpProtocol

    Set-SqlBrowserStartup

    Restart-SqlServices `
        -InstanceName $InstanceName

    $engineServiceName =
        if ($InstanceName -ieq "MSSQLSERVER") {
            "MSSQLSERVER"
        }
        else {
            "MSSQL`$$InstanceName"
        }

    Wait-ServiceRunning `
        -ServiceName $engineServiceName

    $browserService = Get-Service `
        -Name "SQLBrowser" `
        -ErrorAction SilentlyContinue

    if ($null -ne $browserService) {

        Wait-ServiceRunning `
            -ServiceName "SQLBrowser"
    }

    #
    # Refresh WMI objects after restart so verification reads
    # the persisted configuration from SQL Server.
    #
    $managedComputer = Get-ManagedComputer

    $serverInstance = Get-ServerInstance `
        -ManagedComputer $managedComputer `
        -InstanceName $InstanceName

    $tcpProtocol = Get-TcpProtocol `
        -ServerInstance $serverInstance

    Test-NetworkConfiguration `
        -TcpProtocol $tcpProtocol `
        -ExpectedPort $StaticPort

    Test-SqlBrowser

    Write-Host ""
    Write-Success "SQL Server network configuration completed successfully."

}
catch {

    Write-Host ""
    Write-ErrorLog $_.Exception.Message

    throw
}

