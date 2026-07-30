@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 (
    echo.
    echo ERROR: Unable to determine project root.
    exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mssql\cleanup\cleanup_mssql_load_artifacts.ps1"

if errorlevel 1 (
    echo.
    echo =====================================
    echo MSSQL LOAD ARTIFACTS CLEANUP FAILED
    echo =====================================
    echo.
    exit /b 1
)

exit /b 0