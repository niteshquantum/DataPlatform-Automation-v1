@echo off
setlocal
call "%~dp0..\..\common\set_project_root.bat"

if "%CLEANUP_MODE%"=="" (
    set "CLEANUP_MODE=PRESERVE_DATA"
)

if /I not "%CLEANUP_MODE%"=="PRESERVE_DATA" (
    if /I not "%CLEANUP_MODE%"=="DELETE_DATA" (
        echo ERROR: Invalid cleanup mode: %CLEANUP_MODE%
        echo Valid cleanup modes:
        echo   PRESERVE_DATA
        echo   DELETE_DATA
        exit /b 1
    )
)

echo.
echo =====================================
echo POSTGRESQL WINDOWS CLEANUP PIPELINE
echo =====================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\common\Run-CleanupPipeline.ps1" -Database postgresql -CleanupMode "%CLEANUP_MODE%"

if errorlevel 1 (
    echo.
    echo POSTGRESQL CLEANUP FAILED
    exit /b 1
)

echo.
echo =====================================
echo POSTGRESQL CLEANUP SUCCESSFUL
echo =====================================
echo.

exit /b 0
