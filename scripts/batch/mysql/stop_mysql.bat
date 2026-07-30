@echo off

echo.
echo =====================================
echo STOPPING MYSQL
echo =====================================
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0..\..\powershell\stop_mysql.ps1"

if errorlevel 1 (
    echo.
    echo MYSQL STOP FAILED
    exit /b 1
)

echo.
echo MYSQL STOP SUCCESSFUL
echo.