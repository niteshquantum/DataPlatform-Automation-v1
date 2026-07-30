@echo off
setlocal

REM ============================================================
REM GOVERNANCE ACTION PLAN WRAPPER
REM ============================================================

if "%~1"=="" (
    echo.
    echo =====================================
    echo ACTION PLAN ENGINE FAILED
    echo =====================================
    echo Error: Database argument is required.
    echo Usage: run_action_plan.bat database
    echo.
    exit /b 1
)

set "DATABASE=%~1"

echo.
echo =====================================
echo RUNNING GOVERNANCE ACTION PLAN
echo =====================================
echo Database: %DATABASE%
echo.

python scripts\governance\action_plan_engine.py --database "%DATABASE%"

if errorlevel 1 (
    echo.
    echo ACTION PLAN ENGINE WRAPPER FAILED
    exit /b 1
)

echo.
echo ACTION PLAN ENGINE WRAPPER SUCCESSFUL
echo.

endlocal
exit /b 0