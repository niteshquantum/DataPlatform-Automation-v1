@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

powershell -ExecutionPolicy Bypass ^
-File "%PROJECT_ROOT%\scripts\powershell\mongodb\start_mongodb.ps1"

if errorlevel 1 (
    echo.
    echo MONGODB START FAILED
    exit /b 1
)

echo.
echo =====================================
echo MONGODB START SUCCESSFUL
echo =====================================
echo.

exit /b 0