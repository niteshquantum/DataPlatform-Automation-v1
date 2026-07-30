@echo off
setlocal

echo.
echo =====================================
echo DOWNLOADING MSSQL INSTALLATION MEDIA
echo =====================================
echo.

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

REM =====================================
REM DOWNLOAD + EXTRACT MEDIA
REM =====================================

powershell.exe -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mssql\download_media.ps1"

if errorlevel 1 (
    echo.
    echo MSSQL MEDIA DOWNLOAD FAILED
    exit /b 1
)

echo.
echo MSSQL INSTALLATION MEDIA READY
echo.

exit /b 0