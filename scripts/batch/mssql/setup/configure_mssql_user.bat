
@echo off
setlocal

echo.
echo =====================================
echo CONFIGURING MSSQL USER
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass ^
    -File "%PROJECT_ROOT%\scripts\powershell\mssql\setup\configure_mssql_user.ps1"

if errorlevel 1 (
    echo.
    echo MSSQL USER CONFIGURATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo MSSQL USER CONFIGURATION SUCCESSFUL
echo =====================================
echo.

exit /b 0