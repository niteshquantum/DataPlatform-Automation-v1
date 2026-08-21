@echo off

setlocal

call "%~dp0..\..\common\set_project_root.bat"

echo.
echo =====================================
echo MYSQL CLEANUP PIPELINE
echo =====================================
echo.

echo Cleanup Mode : %CLEANUP_MODE%
echo Project Root : %PROJECT_ROOT%
echo.

powershell -NoProfile -ExecutionPolicy Bypass ^
    -File "%PROJECT_ROOT%\scripts\powershell\common\Run-CleanupPipeline.ps1" ^
    -Database mysql ^
    -CleanupMode "%CLEANUP_MODE%"

if errorlevel 1 (

    echo.
    echo MYSQL CLEANUP PIPELINE FAILED
    echo.

    exit /b 1
)

echo.
echo =====================================
echo MYSQL CLEANUP PIPELINE COMPLETED
echo =====================================
echo.

exit /b 0