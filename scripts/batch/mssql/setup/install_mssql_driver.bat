@echo off
setlocal

echo.
echo =====================================
echo INSTALLING MSSQL JDBC DRIVER
echo =====================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0..\..\..\powershell\mssql\download_mssql_driver.ps1"

if errorlevel 1 (
    echo.
    echo ERROR: MSSQL JDBC DRIVER INSTALLATION FAILED
    exit /b 1
)

echo.
echo MSSQL JDBC DRIVER INSTALLATION SUCCESSFUL
echo.

exit /b 0