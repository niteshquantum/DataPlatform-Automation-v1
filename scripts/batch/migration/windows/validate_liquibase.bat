@echo off
setlocal

REM =====================================
REM PROJECT ROOT
REM =====================================

call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 (
    echo ERROR: PROJECT ROOT INITIALIZATION FAILED
    exit /b 1
)

set "ROOT=%PROJECT_ROOT%"

REM =====================================
REM ARGUMENTS
REM =====================================

set "DB_TYPE=%~1"

if "%DB_TYPE%"=="" (
    echo ERROR: Database type not provided
    echo Usage: validate_liquibase.bat ^<DB_TYPE^>
    exit /b 1
)

set "CONFIG_FILE=%ROOT%\config\windows\migration\%DB_TYPE%.conf"

if not exist "%CONFIG_FILE%" (
    echo ERROR: MIGRATION CONFIG NOT FOUND
    echo Expected: %CONFIG_FILE%
    exit /b 1
)

REM =====================================
REM VALIDATE LIQUIBASE USING MIGRATION CONFIG
REM =====================================

call "%ROOT%\scripts\batch\common\validate_liquibase.bat" "%CONFIG_FILE%"

if errorlevel 1 (
    echo ERROR: MIGRATION LIQUIBASE VALIDATION FAILED
    exit /b 1
)

echo.
echo =====================================
echo MIGRATION LIQUIBASE VALIDATED
echo =====================================
echo.

exit /b 0
