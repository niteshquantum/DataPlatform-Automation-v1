@echo off

echo.
echo =====================================
echo INSTALLING SQL SERVER
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mssql\install_mssql.ps1"

if errorlevel 1 (
    echo.
    echo SQL SERVER INSTALLATION FAILED
    exit /b 1
)

echo.
echo SQL SERVER INSTALLATION SUCCESSFUL
echo.

exit /b 0