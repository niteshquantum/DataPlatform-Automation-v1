@echo off

echo.
echo =====================================
echo STARTING MYSQL
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mysql\start_mysql.ps1"

if errorlevel 1 (
    echo.
    echo MYSQL START FAILED
    exit /b 1
)

echo.
echo MYSQL START SUCCESSFUL
echo.