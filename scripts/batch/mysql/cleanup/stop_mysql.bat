@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mysql\cleanup\stop_mysql.ps1"

if errorlevel 1 (
    echo MYSQL STOP FAILED
    exit /b 1
)

exit /b 0