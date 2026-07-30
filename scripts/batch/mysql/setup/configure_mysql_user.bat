
@echo off
setlocal

echo.
echo =====================================
echo CONFIGURING MYSQL USER
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass ^
    -File "%PROJECT_ROOT%\scripts\powershell\mysql\setup\configure_mysql_user.ps1"

if errorlevel 1 (
    echo.
    echo MYSQL USER CONFIGURATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo MYSQL USER CONFIGURATION SUCCESSFUL
echo =====================================
echo.

exit /b 0