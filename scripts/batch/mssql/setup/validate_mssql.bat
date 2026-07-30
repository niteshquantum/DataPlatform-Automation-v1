@echo off

echo.
echo =====================================
echo VALIDATING SQL SERVER
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mssql\validate_mssql.ps1"

if errorlevel 1 (
    echo.
    echo SQL SERVER VALIDATION FAILED
    exit /b 1
)

echo.
echo SQL SERVER VALIDATION SUCCESSFUL
echo.

exit /b 0