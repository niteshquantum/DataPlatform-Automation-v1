
@echo off
setlocal

echo.
echo =====================================
echo CONFIGURING POSTGRESQL WINDOWS SERVICE
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass ^
-File "%PROJECT_ROOT%\scripts\powershell\postgresql\configure_postgresql_service.ps1"

if errorlevel 1 (
    echo.
    echo POSTGRESQL WINDOWS SERVICE CONFIGURATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo POSTGRESQL WINDOWS SERVICE SUCCESSFUL
echo =====================================
echo.

exit /b 0
