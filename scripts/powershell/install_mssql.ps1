$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "====================================="
Write-Host "INSTALLING MSSQL SERVER"
Write-Host "====================================="
Write-Host ""

$service = Get-Service MSSQLSERVER -ErrorAction SilentlyContinue

if ($service) {
Write-Host "SQL Server already installed."
exit 0
}

$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

$downloadDir = Join-Path $root "databases\sqlserver\downloads"

if (!(Test-Path $downloadDir)) {
New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null
}

$installer = Join-Path $downloadDir "SQLServer2022-DEV-x64-ENU.exe"

if (!(Test-Path $installer)) {

    
    Write-Host ""
    Write-Host "Downloading SQL Server..."
    Write-Host ""

    Invoke-WebRequest `
        -Uri "https://download.microsoft.com/download/3/8/d/38de7036-2433-4207-8eae-06e247e17b25/SQLServer2022-DEV-x64-ENU.exe" `
        -OutFile $installer


}

Write-Host ""
Write-Host "Installing SQL Server..."
Write-Host ""

$args = @(
"/Q",
"/ACTION=Install",
"/FEATURES=SQLEngine",
"/INSTANCENAME=MSSQLSERVER",
"/SECURITYMODE=SQL",
"/SAPWD=TerraformSA@2022!",
"/SQLSVCSTARTUPTYPE=Automatic",
"/TCPENABLED=1",
"/IACCEPTSQLSERVERLICENSETERMS"
)

$process = Start-Process `    -FilePath $installer`
-ArgumentList $args `    -Wait`
-PassThru

if ($process.ExitCode -ne 0 -and $process.ExitCode -ne 3010) {

    
    throw "SQL Server installation failed. ExitCode=$($process.ExitCode)"
    

}

Write-Host ""
Write-Host "SQL Server installation completed."
Write-Host ""

exit 0
