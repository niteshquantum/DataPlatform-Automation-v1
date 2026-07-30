@echo off
setlocal

REM ============================================================
REM MIGRATION RECOMMENDATION WRAPPER
REM ============================================================

if "%~1"=="" (
    echo.
    echo =====================================
    echo RECOMMENDATION ENGINE FAILED
    echo =====================================
    echo Error: Database argument is required.
    echo Usage: run_recommendation.bat database
    echo.
    exit /b 1
)

set "DATABASE=%~1"

echo.
echo =====================================
echo RUNNING RECOMMENDATION ENGINE
echo =====================================
echo Database: %DATABASE%
echo.

python scripts\recommendation\recommendation_engine.py --database "%DATABASE%"

if errorlevel 1 (
    echo.
    echo RECOMMENDATION ENGINE WRAPPER FAILED
    exit /b 1
)

echo.
echo RECOMMENDATION ENGINE WRAPPER SUCCESSFUL
echo.

endlocal
exit /b 0