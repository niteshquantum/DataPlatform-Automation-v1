
@echo off
setlocal

echo.
echo =====================================
echo CONFIGURING MONGODB WINDOWS SERVICE
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass ^
-File "%PROJECT_ROOT%\scripts\powershell\mongodb\configure_mongodb_service.ps1"

if errorlevel 1 (
    echo.
    echo MONGODB WINDOWS SERVICE CONFIGURATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo MONGODB WINDOWS SERVICE SUCCESSFUL
echo =====================================
echo.

exit /b 0
