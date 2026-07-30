@echo off
setlocal

REM ============================================================
REM DATA PROFILING WRAPPER
REM ============================================================

if "%~1"=="" (
    echo.
    echo =====================================
    echo DATA PROFILING FAILED
    echo =====================================
    echo Error: Database argument is required.
    echo Usage: run_data_profiling.bat database
    echo.
    exit /b 1
)

set "DATABASE=%~1"

echo.
echo =====================================
echo RUNNING DATA PROFILING
echo =====================================
echo Database: %DATABASE%
echo.

python scripts\profiling\data_profiler.py --database "%DATABASE%"

if errorlevel 1 (
    echo.
    echo DATA PROFILING WRAPPER FAILED
    exit /b 1
)

echo.
echo DATA PROFILING WRAPPER SUCCESSFUL
echo.

endlocal
exit /b 0