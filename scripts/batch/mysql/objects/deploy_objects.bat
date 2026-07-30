@echo off
setlocal EnableDelayedExpansion

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
echo MYSQL DATABASE OBJECT AUTOMATION
echo =====================================
echo.


REM =====================================
REM GENERATE DATABASE OBJECTS
REM =====================================

echo.
echo -------------------------------------
echo GENERATING DATABASE OBJECTS
echo -------------------------------------
echo.

python scripts\python\common\objects\bootstrap_generator.py mysql

if errorlevel 1 (
    echo ERROR: DATABASE OBJECT GENERATION FAILED
    exit /b 1
)


REM =====================================
REM DEPLOY DATABASE OBJECTS
REM =====================================

echo.
echo -------------------------------------
echo DEPLOYING DATABASE OBJECTS
echo -------------------------------------
echo.

python scripts\python\common\objects\deploy_objects.py mysql

if errorlevel 1 (
    echo ERROR: DATABASE OBJECT DEPLOYMENT FAILED
    exit /b 1
)


echo.
echo =====================================
echo MYSQL OBJECT AUTOMATION SUCCESSFUL
echo =====================================
echo.

exit /b 0