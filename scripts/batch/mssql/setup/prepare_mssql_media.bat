@echo off

echo.
echo =====================================
echo PREPARING SQL SERVER INSTALLATION MEDIA
echo =====================================
echo.

call "%~dp0..\..\common\set_project_root.bat"

powershell -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mssql\prepare_mssql_media.ps1"

if errorlevel 1 (
    echo.
    echo PREPARATION OF INSTALLATION MEDIA FAILED
    exit /b 1
)

echo.
echo INSTALLATION MEDIA PREPARED SUCCESSFULLY
echo.

exit /b 0