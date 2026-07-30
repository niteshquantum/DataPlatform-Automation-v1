
@echo off
setlocal

echo.
echo =====================================
echo CONFIGURING MYSQL WINDOWS SERVICE
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass ^
-File "%PROJECT_ROOT%\scripts\powershell\mysql\configure_mysql_service.ps1"

if errorlevel 1 (
    echo.
    echo MYSQL WINDOWS SERVICE CONFIGURATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo MYSQL WINDOWS SERVICE SUCCESSFUL
echo =====================================
echo.

exit /b 0
