@echo off
setlocal

REM ============================================================
REM MIGRATION ANALYSIS END-TO-END ORCHESTRATOR
REM ============================================================

if "%~1"=="" (
    echo.
    echo =====================================
    echo MIGRATION ANALYSIS FAILED
    echo =====================================
    echo Error: Database argument is required.
    echo Usage: run_migration_analysis.bat database
    echo.
    exit /b 1
)

set "DATABASE=%~1"

echo.
echo ============================================================
echo MIGRATION ANALYSIS PIPELINE STARTED
echo ============================================================
echo Database: %DATABASE%
echo.


REM ============================================================
REM STEP 1 - DATA PROFILING
REM ============================================================

call scripts\batch\common\migration\run_data_profiling.bat "%DATABASE%"

if errorlevel 1 (
    echo.
    echo Migration analysis failed during DATA PROFILING.
    exit /b 1
)


REM ============================================================
REM STEP 2 - DATA RECONCILIATION
REM ============================================================

call scripts\batch\common\migration\run_reconciliation.bat "%DATABASE%"

if errorlevel 1 (
    echo.
    echo Migration analysis failed during DATA RECONCILIATION.
    exit /b 1
)


REM ============================================================
REM STEP 3 - MIGRATION ASSESSMENT
REM ============================================================

call scripts\batch\common\migration\run_assessment.bat "%DATABASE%"

if errorlevel 1 (
    echo.
    echo Migration analysis failed during MIGRATION ASSESSMENT.
    exit /b 1
)


REM ============================================================
REM STEP 4 - RECOMMENDATION ENGINE
REM ============================================================

call scripts\batch\common\migration\run_recommendation.bat "%DATABASE%"

if errorlevel 1 (
    echo.
    echo Migration analysis failed during RECOMMENDATION ENGINE.
    exit /b 1
)


REM ============================================================
REM STEP 5 - GOVERNANCE ACTION PLAN
REM ============================================================

call scripts\batch\common\migration\run_action_plan.bat "%DATABASE%"

if errorlevel 1 (
    echo.
    echo Migration analysis failed during GOVERNANCE ACTION PLAN.
    exit /b 1
)


REM ============================================================
REM STEP 6 - TECHNICAL REPORT
REM ============================================================

call scripts\batch\common\migration\generate_technical_report.bat "%DATABASE%"

if errorlevel 1 (
    echo.
    echo Migration analysis failed during TECHNICAL REPORT.
    exit /b 1
)


REM ============================================================
REM STEP 7 - EXECUTIVE REPORT
REM ============================================================

call scripts\batch\common\migration\generate_executive_report.bat "%DATABASE%"

if errorlevel 1 (
    echo.
    echo Migration analysis failed during EXECUTIVE REPORT.
    exit /b 1
)


echo.
echo ============================================================
echo MIGRATION ANALYSIS PIPELINE COMPLETED SUCCESSFULLY
echo ============================================================
echo Database: %DATABASE%
echo.
echo Generated Outputs:
echo   metadata\profiling\%DATABASE%\profiling.json
echo   metadata\reconciliation\%DATABASE%\reconciliation.json
echo   metadata\assessment\%DATABASE%\assessment.json
echo   metadata\recommendation\%DATABASE%\recommendation.json
echo   metadata\governance\%DATABASE%\action_plan.json
echo   reports\migration\%DATABASE%\technical_report.html
echo   reports\migration\%DATABASE%\executive_report.html
echo.

endlocal
exit /b 0