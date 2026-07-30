@echo off
setlocal

echo.
echo =====================================
echo INSTALLING SQL SERVER
echo =====================================
echo.

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

powershell.exe -ExecutionPolicy Bypass ^
-File "%PROJECT_ROOT%\scripts\powershell\mssql\install_mssql_gdrive.ps1"

if errorlevel 1 (
    echo.
    echo SQL SERVER INSTALLATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo SQL SERVER INSTALLATION SUCCESSFUL
echo =====================================
echo.

exit /b 0