@echo off

echo.
echo =====================================
echo CREATE DATABASE
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mssql\create_database.ps1"

if errorlevel 1 (
    echo.
    echo DATABASE CREATION FAILED
    exit /b 1
)

echo.
echo DATABASE CREATED SUCCESSFULLY
echo.

exit /b 0