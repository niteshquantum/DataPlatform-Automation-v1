@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\postgresql\cleanup\stop_postgresql.ps1"

if errorlevel 1 (
    echo POSTGRESQL STOP FAILED
    exit /b 1
)

exit /b 0