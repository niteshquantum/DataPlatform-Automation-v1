@echo off
setlocal

REM ============================================================
REM DATA RECONCILIATION WRAPPER
REM ============================================================

if "%~1"=="" (
    echo.
    echo =====================================
    echo DATA RECONCILIATION FAILED
    echo =====================================
    echo Error: Database argument is required.
    echo Usage: run_reconciliation.bat database
    echo.
    exit /b 1
)

set "DATABASE=%~1"

echo.
echo =====================================
echo RUNNING DATA RECONCILIATION
echo =====================================
echo Database: %DATABASE%
echo.

python scripts\reconciliation\reconciliation_engine.py --database "%DATABASE%"

if errorlevel 1 (
    echo.
    echo DATA RECONCILIATION WRAPPER FAILED
    exit /b 1
)

echo.
echo DATA RECONCILIATION WRAPPER SUCCESSFUL
echo.

endlocal
exit /b 0