@echo off

setlocal EnableExtensions

call "%~dp0..\..\common\set_project_root.bat"

echo.
echo =====================================
echo MYSQL CLEANUP PIPELINE
echo =====================================
echo.

echo Cleanup Mode : %CLEANUP_MODE%
echo.

if "%CLEANUP_MODE%"=="" (
    echo ERROR: CLEANUP_MODE is not set
    exit /b 1
)

if /I "%CLEANUP_MODE%"=="PRESERVE_DATA" goto VALID_MODE
if /I "%CLEANUP_MODE%"=="DELETE_DATA" goto VALID_MODE
if /I "%CLEANUP_MODE%"=="RESET_SCHEMA_CONTEXT" goto VALID_MODE

echo ERROR: Invalid cleanup mode: %CLEANUP_MODE%
echo Valid modes: PRESERVE_DATA, DELETE_DATA or RESET_SCHEMA_CONTEXT

exit /b 1


:VALID_MODE

powershell -NoProfile -ExecutionPolicy Bypass ^
    -File "%PROJECT_ROOT%\scripts\powershell\common\Run-CleanupPipeline.ps1" ^
    -Database mysql ^
    -CleanupMode "%CLEANUP_MODE%"

if errorlevel 1 (

    echo.
    echo MYSQL CLEANUP PIPELINE FAILED

    exit /b 1
)

echo.
echo =====================================
echo MYSQL CLEANUP PIPELINE COMPLETED
echo =====================================
echo.

exit /b 0