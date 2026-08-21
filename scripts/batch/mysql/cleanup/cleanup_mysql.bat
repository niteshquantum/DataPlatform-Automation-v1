@echo off

setlocal

call "%~dp0..\..\common\set_project_root.bat"

REM =====================================
REM DEFAULT CLEANUP MODE
REM =====================================

if "%CLEANUP_MODE%"=="" (
    set "CLEANUP_MODE=PRESERVE_DATA"
)


REM =====================================
REM VALIDATE CLEANUP MODE
REM =====================================

if /I "%CLEANUP_MODE%"=="PRESERVE_DATA" goto VALID_MODE

if /I "%CLEANUP_MODE%"=="DELETE_DATA" goto VALID_MODE

if /I "%CLEANUP_MODE%"=="RESET_SCHEMA_CONTEXT" goto VALID_MODE


echo ERROR: Invalid cleanup mode: %CLEANUP_MODE%
echo Valid modes: PRESERVE_DATA, DELETE_DATA or RESET_SCHEMA_CONTEXT

exit /b 1


:VALID_MODE

echo.
echo =====================================
echo MYSQL WINDOWS CLEANUP
echo =====================================
echo.

echo Cleanup Mode : %CLEANUP_MODE%
echo Project Root : %PROJECT_ROOT%
echo.


REM =====================================
REM RUN CLEANUP ORCHESTRATOR
REM =====================================

powershell -NoProfile -ExecutionPolicy Bypass ^
    -File "%PROJECT_ROOT%\scripts\powershell\common\Run-CleanupPipeline.ps1" ^
    -Database mysql ^
    -CleanupMode "%CLEANUP_MODE%"


if errorlevel 1 (

    echo.
    echo MYSQL CLEANUP FAILED
    echo.

    exit /b 1
)


echo.
echo =====================================
echo MYSQL CLEANUP SUCCESSFUL
echo =====================================
echo.

exit /b 0