Write-Host "==================================="
Write-Host "Stopping MongoDB"
Write-Host "==================================="

try {

    Stop-Service MongoDB

    Write-Host "MongoDB Stopped Successfully"

}
catch {

    Write-Host "MongoDB Service already stopped"

}