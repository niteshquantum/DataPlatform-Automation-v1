@echo off

echo.
echo =====================================
echo GENERATING SQL SERVER CONFIGURATION FILE
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mssql\generate_configuration_file.ps1"

if errorlevel 1 (
    echo.
    echo CONFIGURATION FILE GENERATION FAILED
    exit /b 1
)

echo.
echo CONFIGURATION FILE GENERATED SUCCESSFULLY
echo.

exit /b 0