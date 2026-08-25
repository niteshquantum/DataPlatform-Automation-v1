@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\postgresql\cleanup\reset_terraform_state.ps1"

if errorlevel 1 (
    echo POSTGRESQL TERRAFORM STATE RESET FAILED
    exit /b 1
)

exit /b 0