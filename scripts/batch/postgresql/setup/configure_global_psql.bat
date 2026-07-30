
@echo off
setlocal

echo.
echo =====================================
echo CONFIGURING GLOBAL PSQL COMMAND
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass ^
-File "%PROJECT_ROOT%\scripts\powershell\postgresql\configure_global_psql.ps1"

if errorlevel 1 (
    echo.
    echo GLOBAL PSQL CONFIGURATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo GLOBAL PSQL CONFIGURATION SUCCESSFUL
echo =====================================
echo.

exit /b 0
