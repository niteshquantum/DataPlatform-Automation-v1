@echo off
setlocal

echo.
echo =====================================
echo INSTALLING POSTGRESQL JDBC DRIVER
echo =====================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0..\..\..\powershell\postgresql\download_postgresql_driver.ps1"

if errorlevel 1 (
    echo.
    echo ERROR: POSTGRESQL JDBC DRIVER INSTALLATION FAILED
    exit /b 1
)

echo.
echo POSTGRESQL JDBC DRIVER INSTALLATION SUCCESSFUL
echo.

exit /b 0