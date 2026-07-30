@echo off
setlocal

echo.
echo =====================================
echo CREATE DATABASE
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

python "%PROJECT_ROOT%\scripts\python\postgresql\setup\create_database.py"

if errorlevel 1 (
    echo.
    echo DATABASE CREATION FAILED
    exit /b 1
)

echo.
echo DATABASE READY
echo.

exit /b 0