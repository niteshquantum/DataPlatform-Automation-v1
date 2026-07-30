@echo off

echo.
echo =====================================
echo CONFIGURING SQL SERVER
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mssql\configure_mssql.ps1"

if errorlevel 1 (
    echo.
    echo SQL SERVER CONFIGURATION FAILED
    exit /b 1
)

echo.
echo SQL SERVER CONFIGURATION SUCCESSFUL
echo.

exit /b 0