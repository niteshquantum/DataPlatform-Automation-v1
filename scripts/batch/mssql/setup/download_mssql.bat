@echo off

echo.
echo =====================================
echo DOWNLOADING SQL SERVER
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mssql\download_mssql.ps1"

if errorlevel 1 (
    echo.
    echo SQL SERVER DOWNLOAD FAILED
    exit /b 1
)

echo.
echo SQL SERVER DOWNLOAD SUCCESSFUL
echo.

exit /b 0