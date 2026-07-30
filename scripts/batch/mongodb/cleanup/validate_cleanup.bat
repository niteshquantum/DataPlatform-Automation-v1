@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

echo.
echo =====================================
echo VALIDATING MONGODB CLEANUP
echo =====================================
echo.

if "%CLEANUP_MODE%"=="" (
    echo ERROR: CLEANUP_MODE is not set.
    exit /b 1
)

powershell -ExecutionPolicy Bypass ^
-File "%PROJECT_ROOT%\scripts\powershell\mongodb\cleanup\validate_cleanup.ps1"

if errorlevel 1 (
    echo.
    echo =====================================
    echo MONGODB CLEANUP VALIDATION FAILED
    echo =====================================
    echo.
    exit /b 1
)

echo.
echo =====================================
echo MONGODB CLEANUP VALIDATION SUCCESSFUL
echo =====================================
echo.

exit /b 0