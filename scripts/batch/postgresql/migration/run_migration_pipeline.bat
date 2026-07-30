@echo off
setlocal

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 (
    echo ERROR: PROJECT ROOT SETUP FAILED
    exit /b 1
)

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"


echo.
echo =====================================
echo DISCOVERY ^& MIGRATION REPORTING PIPELINE
echo =====================================
echo.


REM =====================================
REM DISCOVER DATABASE ENVIRONMENT
REM =====================================

echo.
echo -------------------------------------
echo DISCOVER DATABASE ENVIRONMENT
echo -------------------------------------
echo.

python "%PROJECT_ROOT%\scripts\discovery\discovery_engine.py" --database postgresql

if errorlevel 1 (
    echo.
    echo ERROR: DISCOVERY FAILED
    echo.
    exit /b 1
)


REM =====================================
REM ANALYZE DATABASE GROWTH
REM =====================================

echo.
echo -------------------------------------
echo ANALYZE DATABASE GROWTH
echo -------------------------------------
echo.

python "%PROJECT_ROOT%\scripts\discovery\growth_analyzer.py" --database postgresql

if errorlevel 1 (
    echo.
    echo ERROR: GROWTH ANALYSIS FAILED
    echo.
    exit /b 1
)


REM =====================================
REM ANALYZE MIGRATION REQUIREMENTS
REM =====================================

echo.
echo -------------------------------------
echo ANALYZE MIGRATION REQUIREMENTS
echo -------------------------------------
echo.

python "%PROJECT_ROOT%\scripts\discovery\requirement_analyzer.py" --database postgresql

if errorlevel 1 (
    echo.
    echo ERROR: REQUIREMENT ANALYSIS FAILED
    echo.
    exit /b 1
)


REM =====================================
REM ASSESS MIGRATION
REM =====================================

echo.
echo -------------------------------------
echo ASSESS MIGRATION
echo -------------------------------------
echo.

python "%PROJECT_ROOT%\scripts\assessment\assessment_engine.py" --database postgresql

if errorlevel 1 (
    echo.
    echo ERROR: MIGRATION ASSESSMENT FAILED
    echo.
    exit /b 1
)


REM =====================================
REM GENERATE MIGRATION RECOMMENDATIONS
REM =====================================

echo.
echo -------------------------------------
echo GENERATE MIGRATION RECOMMENDATIONS
echo -------------------------------------
echo.

python "%PROJECT_ROOT%\scripts\recommendation\recommendation_engine.py" --database postgresql

if errorlevel 1 (
    echo.
    echo ERROR: RECOMMENDATION GENERATION FAILED
    echo.
    exit /b 1
)


REM =====================================
REM GENERATE GOVERNANCE ACTION PLAN
REM =====================================

echo.
echo -------------------------------------
echo GENERATE GOVERNANCE ACTION PLAN
echo -------------------------------------
echo.

python "%PROJECT_ROOT%\scripts\governance\action_plan_engine.py" --database postgresql

if errorlevel 1 (
    echo.
    echo ERROR: ACTION PLAN GENERATION FAILED
    echo.
    exit /b 1
)


REM =====================================
REM GENERATE TECHNICAL MIGRATION REPORT
REM =====================================

echo.
echo -------------------------------------
echo GENERATE TECHNICAL MIGRATION REPORT
echo -------------------------------------
echo.

python "%PROJECT_ROOT%\scripts\reporting\migration\technical_report.py" --database postgresql

if errorlevel 1 (
    echo.
    echo ERROR: TECHNICAL REPORT GENERATION FAILED
    echo.
    exit /b 1
)


REM =====================================
REM GENERATE EXECUTIVE MIGRATION REPORT
REM =====================================

echo.
echo -------------------------------------
echo GENERATE EXECUTIVE MIGRATION REPORT
echo -------------------------------------
echo.

python "%PROJECT_ROOT%\scripts\reporting\migration\executive_report.py" --database postgresql

if errorlevel 1 (
    echo.
    echo ERROR: EXECUTIVE REPORT GENERATION FAILED
    echo.
    exit /b 1
)


echo.
echo =====================================
echo DISCOVERY ^& MIGRATION REPORTING COMPLETED
echo =====================================
echo.

exit /b 0
