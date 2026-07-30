
@echo off
setlocal

echo.
echo =====================================
echo CONFIGURING POSTGRESQL USER
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass ^
    -File "%PROJECT_ROOT%\scripts\powershell\postgresql\setup\configure_postgresql_user.ps1"

if errorlevel 1 (
    echo.
    echo POSTGRESQL USER CONFIGURATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo POSTGRESQL USER CONFIGURATION SUCCESSFUL
echo =====================================
echo.

exit /b 0