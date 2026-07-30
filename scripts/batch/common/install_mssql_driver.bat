@echo off
setlocal

echo.
echo =====================================
echo INSTALLING MSSQL JDBC DRIVER
echo =====================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0..\..\powershell\download_mssql_driver.ps1"

if errorlevel 1 (
echo MSSQL DRIVER INSTALLATION FAILED
exit /b 1
)

echo.
echo MSSQL DRIVER INSTALLATION SUCCESSFUL
echo.

exit /b 0