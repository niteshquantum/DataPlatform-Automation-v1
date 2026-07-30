@echo off
setlocal

REM ============================================================
REM TECHNICAL MIGRATION REPORT WRAPPER
REM ============================================================

if "%~1"=="" (
    echo.
    echo =====================================
    echo TECHNICAL REPORT GENERATION FAILED
    echo =====================================
    echo Error: Database argument is required.
    echo Usage: generate_technical_report.bat database
    echo.
    exit /b 1
)

set "DATABASE=%~1"

echo.
echo =====================================
echo GENERATING TECHNICAL MIGRATION REPORT
echo =====================================
echo Database: %DATABASE%
echo.

python scripts\reporting\migration\technical_report.py --database "%DATABASE%"

if errorlevel 1 (
    echo.
    echo TECHNICAL REPORT WRAPPER FAILED
    exit /b 1
)

echo.
echo TECHNICAL REPORT WRAPPER SUCCESSFUL
echo.

endlocal
exit /b 0