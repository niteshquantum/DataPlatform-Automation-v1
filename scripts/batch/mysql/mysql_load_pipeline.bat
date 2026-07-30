@echo off
setlocal EnableDelayedExpansion

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\common\set_project_root.bat"

if errorlevel 1 (
    echo ERROR: PROJECT ROOT SETUP FAILED
    exit /b 1
)

cd /d "%PROJECT_ROOT%"


echo.
echo =====================================
echo MYSQL AUTOMATION PIPELINE
echo =====================================
echo.


REM =====================================
REM VALIDATE PYTHON RUNTIME
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\common\validate_python_runtime.bat"

if errorlevel 1 (
    echo ERROR: PYTHON RUNTIME VALIDATION FAILED
    exit /b 1
)


REM =====================================
REM VALIDATE PYTHON REQUIREMENTS
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mysql\setup\validate_python_requirements.bat"

if errorlevel 1 (
    echo ERROR: PYTHON REQUIREMENTS VALIDATION FAILED
    exit /b 1
)


REM =====================================
REM START MYSQL
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mysql\setup\start_mysql.bat"

if errorlevel 1 (
    echo ERROR: MYSQL START FAILED
    exit /b 1
)


REM =====================================
REM VALIDATE MYSQL
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mysql\setup\validate_mysql.bat"

if errorlevel 1 (
    echo ERROR: MYSQL VALIDATION FAILED
    exit /b 1
)


REM =====================================
REM CREATE DATABASE
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mysql\setup\create_database.bat"

if errorlevel 1 (
    echo ERROR: DATABASE CREATION FAILED
    exit /b 1
)


REM =====================================
REM VALIDATE DATABASE
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mysql\load\validate_database.bat"

if errorlevel 1 (
    echo ERROR: DATABASE VALIDATION FAILED
    exit /b 1
)


REM =====================================
REM DOWNLOAD DATASET
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\common\download_dataset.bat"

if errorlevel 1 (
    echo ERROR: DATASET DOWNLOAD FAILED
    exit /b 1
)


REM =====================================
REM DEPLOY SCHEMA
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mysql\load\deploy_schema.bat"

if errorlevel 1 (
    echo ERROR: SCHEMA DEPLOYMENT FAILED
    exit /b 1
)


REM =====================================
REM VALIDATE SCHEMA
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mysql\load\validate_schema.bat"

if errorlevel 1 (
    echo ERROR: SCHEMA VALIDATION FAILED
    exit /b 1
)


REM =====================================
REM CDC CHECK
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mysql\load\run_cdc.bat"

if errorlevel 100 (
    echo.
    echo SKIPPING DATA LOAD — NO CDC CHANGES
    echo.
    goto :skip_data_load
)

if errorlevel 1 (
    echo ERROR: CDC CHECK FAILED
    exit /b 1
)


REM =====================================
REM VALIDATE SOURCE DATA
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mysql\load\validate_source.bat"

if errorlevel 1 (
    echo ERROR: SOURCE DATA VALIDATION FAILED
    exit /b 1
)


REM =====================================
REM LOAD DATA
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mysql\load\load_data.bat"

if errorlevel 1 (
    echo ERROR: DATA LOAD FAILED
    exit /b 1
)

:skip_data_load


REM =====================================
REM DEPLOY DATABASE OBJECTS
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mysql\objects\deploy_objects.bat"

if errorlevel 1 (
    echo ERROR: DATABASE OBJECT DEPLOYMENT FAILED
    exit /b 1
)


@REM REM =====================================
@REM REM VALIDATE DATABASE OBJECTS
@REM REM =====================================
call "%PROJECT_ROOT%\scripts\batch\mysql\objects\validate_objects.bat"

if errorlevel 1 (
    echo ERROR: DATABASE OBJECTS VALIDATION FAILED
    exit /b 1
)

@REM REM =====================================
@REM REM DATABASE ASSESSMENT
@REM REM =====================================

@REM call "%PROJECT_ROOT%\scripts\batch\mysql\assessment\run_assessment.bat" all

@REM if errorlevel 1 (
@REM     echo ERROR: DATABASE ASSESSMENT FAILED
@REM     exit /b 1
@REM )


@REM REM =====================================
@REM REM GENERATE ASSESSMENT REPORT
@REM REM =====================================

@REM call "%PROJECT_ROOT%\scripts\batch\common\generate_assessment_report.bat"

@REM if errorlevel 1 (
@REM     echo ERROR: ASSESSMENT REPORT GENERATION FAILED
@REM     exit /b 1
@REM )


echo.
echo =====================================
echo MYSQL AUTOMATION PIPELINE SUCCESSFUL
echo =====================================
echo.

exit /b 0
