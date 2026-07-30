
@echo off
setlocal

echo.
echo =====================================
echo CONFIGURING GLOBAL MONGOSH COMMAND
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -NoProfile -ExecutionPolicy Bypass ^
-File "%PROJECT_ROOT%\scripts\powershell\mongodb\configure_global_mongosh.ps1"

if errorlevel 1 (
    echo.
    echo GLOBAL MONGOSH CONFIGURATION FAILED
    exit /b 1
)

echo.
echo GLOBAL MONGOSH CONFIGURATION SUCCESSFUL
echo.

exit /b 0

