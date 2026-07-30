@echo off
setlocal

REM ============================================================
REM MIGRATION ASSESSMENT WRAPPER
REM ============================================================

if "%~1"=="" (
    echo.
    echo =====================================
    echo MIGRATION ASSESSMENT FAILED
    echo =====================================
    echo Error: Database argument is required.
    echo Usage: run_assessment.bat database
    echo.
    exit /b 1
)

set "DATABASE=%~1"

echo.
echo =====================================
echo RUNNING MIGRATION ASSESSMENT
echo =====================================
echo Database: %DATABASE%
echo.

python scripts\assessment\assessment_engine.py --database "%DATABASE%"

if errorlevel 1 (
    echo.
    echo MIGRATION ASSESSMENT WRAPPER FAILED
    exit /b 1
)

echo.
echo MIGRATION ASSESSMENT WRAPPER SUCCESSFUL
echo.

endlocal
exit /b 0