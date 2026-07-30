@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mysql\cleanup\cleanup_mysql_load_artifacts.ps1"

if errorlevel 1 (
    echo.
    echo MYSQL LOAD ARTIFACTS CLEANUP FAILED
    exit /b 1
)

exit /b 0