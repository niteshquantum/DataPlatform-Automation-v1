@echo off

echo.
echo =====================================
echo STARTING SQL SERVER
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mssql\start_mssql.ps1"

if errorlevel 1 (
    echo.
    echo SQL SERVER START FAILED
    exit /b 1
)

echo.
echo SQL SERVER START SUCCESSFUL
echo.

exit /b 0