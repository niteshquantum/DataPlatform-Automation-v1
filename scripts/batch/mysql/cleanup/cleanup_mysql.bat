@echo off
setlocal
call "%~dp0..\..\common\set_project_root.bat"

if "%CLEANUP_MODE%"=="" (
    set "CLEANUP_MODE=PRESERVE_DATA"
)

if /I not "%CLEANUP_MODE%"=="PRESERVE_DATA" (
    if /I not "%CLEANUP_MODE%"=="DELETE_DATA" (
        echo ERROR: Invalid cleanup mode: %CLEANUP_MODE%
        echo Valid modes: PRESERVE_DATA or DELETE_DATA
        exit /b 1
    )
)

echo.
echo =====================================
echo MYSQL WINDOWS CLEANUP
echo =====================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\common\Run-CleanupPipeline.ps1" -Database mysql -CleanupMode "%CLEANUP_MODE%"

if errorlevel 1 (
    echo.
    echo MYSQL CLEANUP FAILED
    exit /b 1
)

echo.
echo =====================================
echo MYSQL CLEANUP SUCCESSFUL
echo =====================================
echo.

exit /b 0
