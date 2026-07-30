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
echo MSSQL AUTOMATION PIPELINE
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
REM INSTALL PYTHON REQUIREMENTS
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mssql\setup\install_python_requirements.bat"

if errorlevel 1 (
    echo ERROR: PYTHON REQUIREMENTS INSTALLATION FAILED
    exit /b 1
)


REM =====================================
REM VALIDATE PYTHON REQUIREMENTS
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mssql\setup\validate_python_requirements.bat"

if errorlevel 1 (
    echo ERROR: PYTHON REQUIREMENTS VALIDATION FAILED
    exit /b 1
)


REM =====================================
REM VALIDATE JAVA RUNTIME
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\common\validate_java_runtime.bat"

if errorlevel 1 (
    echo ERROR: JAVA RUNTIME VALIDATION FAILED
    exit /b 1
)


REM =====================================
REM INSTALL TOOLS
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mssql\setup\install_tools.bat"

if errorlevel 1 (
    echo ERROR: TOOL INSTALLATION FAILED
    exit /b 1
)


REM =====================================
REM CHECK INSTANCE STATE
REM =====================================

set "INST_INSTANCE_STATE="

for /f "tokens=1* delims==" %%A in ('"%PROJECT_ROOT%\scripts\batch\mssql\setup\check_instance.bat"') do (
    set "INST_%%A=%%B"
)

if not defined INST_INSTANCE_STATE (
    echo ERROR: Failed to determine instance state.
    exit /b 1
)

echo Instance State: %INST_INSTANCE_STATE%

if /I "%INST_INSTANCE_STATE%"=="NO_INSTANCE" (
    echo.
    echo =====================================
    echo DEPLOYING SQL SERVER
    echo =====================================
    echo.
    call "%PROJECT_ROOT%\scripts\batch\mssql\setup\deploy_mssql_gdrive.bat"
    if errorlevel 1 exit /b 1

    echo.
    echo =====================================
    echo CHECKING ADMINISTRATOR PRIVILEGES FOR CONFIGURATION
    echo =====================================
    echo.

    set "LOAD_ADMIN_STATUS="

    call "%PROJECT_ROOT%\scripts\batch\common\check_admin_privileges.bat"
    if errorlevel 1 (
        set "LOAD_ADMIN_STATUS=false"
    ) else (
        set "LOAD_ADMIN_STATUS=true"
    )

    echo Administrator Status: %LOAD_ADMIN_STATUS%

    if /I "%LOAD_ADMIN_STATUS%"=="true" (
        echo.
        echo =====================================
        echo CONFIGURING SQL SERVER
        echo =====================================
        echo.
        call "%PROJECT_ROOT%\scripts\batch\mssql\setup\configure_mssql.bat"
        if errorlevel 1 exit /b 1
    ) else (
        echo Administrator privileges not available.
        echo SQL Server network configuration will be skipped.
    )
)

if /I "%INST_INSTANCE_STATE%"=="INSTANCE_INSTALLED_BUT_STOPPED" (
    echo Starting existing SQL Server instance.
)

if /I "%INST_INSTANCE_STATE%"=="INSTANCE_RUNNING_AND_USABLE" (
    echo Reusing existing SQL Server instance.
)


REM =====================================
REM START SQL SERVER
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mssql\setup\start_mssql.bat"

if errorlevel 1 (
    echo ERROR: MSSQL START FAILED
    exit /b 1
)


REM =====================================
REM VALIDATE SQL SERVER
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mssql\setup\validate_mssql.bat"

if errorlevel 1 (
    echo ERROR: MSSQL VALIDATION FAILED
    exit /b 1
)


REM =====================================
REM CREATE DATABASE
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mssql\setup\create_database.bat"

if errorlevel 1 (
    echo ERROR: DATABASE CREATION FAILED
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
REM PROFILE SOURCE DATA
REM =====================================

python scripts\profiling\data_profiler.py --database mssql

if errorlevel 1 (
    echo ERROR: DATA PROFILING FAILED
    exit /b 1
)


REM =====================================
REM CDC CHECK
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mssql\load\run_cdc.bat"

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
REM LOAD DATA
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mssql\load\load_data.bat"

if errorlevel 1 (
    echo ERROR: DATA LOAD FAILED
    exit /b 1
)


REM =====================================
REM VALIDATE LOADED DATA
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mssql\load\validate_loaded_data.bat"

if errorlevel 1 (
    echo ERROR: LOADED DATA VALIDATION FAILED
    exit /b 1
)

:skip_data_load


REM =====================================
REM DEPLOY DATABASE OBJECTS
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mssql\objects\deploy_objects.bat"

if errorlevel 1 (
    echo ERROR: DATABASE OBJECT DEPLOYMENT FAILED
    exit /b 1
)


REM =====================================
REM VALIDATE DATABASE OBJECTS
REM =====================================

call "%PROJECT_ROOT%\scripts\batch\mssql\objects\validate_objects.bat"

if errorlevel 1 (
    echo ERROR: DATABASE OBJECT VALIDATION FAILED
    exit /b 1
)


@REM ============================================================
@REM OPTIONAL POST-PROCESSING
@REM Assessment and migration reporting are orchestrated through
@REM dedicated pipeline wrappers and run as post-LOAD stages.
@REM ============================================================

call "%PROJECT_ROOT%\scripts\batch\mssql\assessment\run_assessment_pipeline.bat"
if errorlevel 1 (
    echo.
    echo ERROR: ASSESSMENT & RECONCILIATION FAILED
    echo.
    exit /b 1
)


@REM REM ============================================================
@REM OPTIONAL POST-PROCESSING
@REM Discovery/migration reporting is orchestrated through
@REM dedicated pipeline wrapper and runs as post-LOAD stage.
@REM ============================================================

call "%PROJECT_ROOT%\scripts\batch\mssql\migration\run_migration_pipeline.bat"
if errorlevel 1 (
    echo.
    echo ERROR: DISCOVERY & MIGRATION REPORTING FAILED
    echo.
    exit /b 1
)


echo.
echo =====================================
echo MSSQL AUTOMATION PIPELINE SUCCESSFUL
echo =====================================
echo.

exit /b 0