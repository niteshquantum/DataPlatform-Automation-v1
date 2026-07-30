
@echo off
setlocal

echo.
echo =====================================
echo CONFIGURING GLOBAL MYSQL COMMAND
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass ^
-File "%PROJECT_ROOT%\scripts\powershell\mysql\configure_global_mysql.ps1"

if errorlevel 1 (
    echo.
    echo GLOBAL MYSQL CONFIGURATION FAILED
    exit /b 1
)

echo.
echo GLOBAL MYSQL CONFIGURATION SUCCESSFUL
echo.

exit /b 0

