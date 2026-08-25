@echo off
setlocal
call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 (
    echo ERROR: Unable to determine a valid project root.
    exit /b 1
)

if "%CLEANUP_MODE%"=="" (
    set "CLEANUP_MODE=PRESERVE_DATA"
)

if /I not "%CLEANUP_MODE%"=="PRESERVE_DATA" (
    if /I not "%CLEANUP_MODE%"=="DELETE_DATA" (
        if /I not "%CLEANUP_MODE%"=="RESET_SCHEMA_CONTEXT" (
            echo ERROR: Invalid cleanup mode: %CLEANUP_MODE%
            echo.
            echo Supported modes:
            echo   RESET_SCHEMA_CONTEXT
            echo   PRESERVE_DATA
            echo   DELETE_DATA
            echo.
            exit /b 1
        )
    )
)

echo.
echo ==========================================
echo MONGODB WINDOWS CLEANUP PIPELINE
echo ==========================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\common\Run-CleanupPipeline.ps1" -Database mongodb -CleanupMode "%CLEANUP_MODE%"

if errorlevel 1 (
    echo.
    echo MONGODB CLEANUP FAILED
    exit /b 1
)

echo.
echo ==========================================
echo MONGODB WINDOWS CLEANUP SUCCESSFUL
echo ==========================================
echo.

exit /b 0
