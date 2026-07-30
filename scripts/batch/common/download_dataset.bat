@echo off
setlocal

echo.
echo =====================================
echo DOWNLOADING DATASET
echo =====================================
echo.

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0set_project_root.bat"

REM =====================================
REM DOWNLOAD DATASET
REM =====================================

powershell.exe -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\common\download_dataset.ps1"

if errorlevel 1 (
    echo.
    echo DATASET DOWNLOAD FAILED
    exit /b 1
)

echo.
echo DATASET READY
echo.

exit /b 0