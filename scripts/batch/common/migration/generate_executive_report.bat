@echo off
setlocal

REM ============================================================
REM EXECUTIVE MIGRATION REPORT WRAPPER
REM ============================================================

if "%~1"=="" (
    echo.
    echo =====================================
    echo EXECUTIVE REPORT GENERATION FAILED
    echo =====================================
    echo Error: Database argument is required.
    echo Usage: generate_executive_report.bat database
    echo.
    exit /b 1
)

set "DATABASE=%~1"

echo.
echo =====================================
echo GENERATING EXECUTIVE MIGRATION REPORT
echo =====================================
echo Database: %DATABASE%
echo.

python scripts\reporting\migration\executive_report.py --database "%DATABASE%"

if errorlevel 1 (
    echo.
    echo EXECUTIVE REPORT WRAPPER FAILED
    exit /b 1
)

echo.
echo EXECUTIVE REPORT WRAPPER SUCCESSFUL
echo.

endlocal
exit /b 0