@echo off
setlocal

echo.
echo =====================================
echo INSTALLING LIQUIBASE
echo =====================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0..\..\powershell\download_liquibase.ps1"

if errorlevel 1 (
    echo.
    echo ERROR: LIQUIBASE INSTALLATION FAILED
    exit /b 1
)

echo.
echo LIQUIBASE INSTALLATION SUCCESSFUL
echo.

exit /b 0
