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
echo ASSESSMENT ^& RECONCILIATION PIPELINE
echo =====================================
echo.


REM =====================================
REM DATABASE ASSESSMENT
REM =====================================

echo.
echo -------------------------------------
echo DATABASE ASSESSMENT
echo -------------------------------------
echo.

call "%PROJECT_ROOT%\scripts\batch\postgresql\assessment\run_assessment.bat" all

if errorlevel 1 (
    echo.
    echo ERROR: DATABASE ASSESSMENT FAILED
    echo.
    exit /b 1
)


REM =====================================
REM ASSESSMENT REPORT
REM =====================================

echo.
echo -------------------------------------
echo ASSESSMENT REPORT
echo -------------------------------------
echo.

call "%PROJECT_ROOT%\scripts\batch\common\generate_assessment_report.bat"

if errorlevel 1 (
    echo.
    echo ERROR: ASSESSMENT REPORT GENERATION FAILED
    echo.
    exit /b 1
)


REM =====================================
REM RECONCILE SOURCE AND TARGET DATA
REM =====================================

echo.
echo -------------------------------------
echo RECONCILE SOURCE AND TARGET DATA
echo -------------------------------------
echo.

python "%PROJECT_ROOT%\scripts\reconciliation\reconciliation_engine.py" --database postgresql

if errorlevel 1 (
    echo.
    echo ERROR: RECONCILIATION FAILED
    echo.
    exit /b 1
)


echo.
echo =====================================
echo ASSESSMENT ^& RECONCILIATION COMPLETED
echo =====================================
echo.

exit /b 0
