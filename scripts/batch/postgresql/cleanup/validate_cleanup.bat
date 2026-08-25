@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\postgresql\cleanup\validate_cleanup.ps1"

if errorlevel 1 (
    echo POSTGRESQL CLEANUP VALIDATION FAILED
    exit /b 1
)

exit /b 0