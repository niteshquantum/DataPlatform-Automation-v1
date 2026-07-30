@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

echo.
echo =====================================
echo STOPPING PROJECT-MANAGED MONGODB
echo =====================================
echo.

powershell -ExecutionPolicy Bypass ^
-File "%PROJECT_ROOT%\scripts\powershell\mongodb\cleanup\stop_mongodb.ps1"

if errorlevel 1 (
    echo.
    echo =====================================
    echo MONGODB STOP FAILED
    echo =====================================
    echo.
    exit /b 1
)

echo.
echo =====================================
echo MONGODB STOP SUCCESSFUL
echo =====================================
echo.

exit /b 0