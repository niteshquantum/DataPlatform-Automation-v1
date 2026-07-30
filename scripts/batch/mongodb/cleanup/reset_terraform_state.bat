@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

echo.
echo =====================================
echo RESETTING MONGODB TERRAFORM STATE
echo =====================================
echo.

powershell -ExecutionPolicy Bypass ^
-File "%PROJECT_ROOT%\scripts\powershell\mongodb\cleanup\reset_terraform_state.ps1"

if errorlevel 1 (
    echo.
    echo =====================================
    echo TERRAFORM STATE RESET FAILED
    echo =====================================
    echo.
    exit /b 1
)

echo.
echo =====================================
echo TERRAFORM STATE RESET SUCCESSFUL
echo =====================================
echo.

exit /b 0