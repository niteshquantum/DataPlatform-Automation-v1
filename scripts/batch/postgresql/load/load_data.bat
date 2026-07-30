@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
set "LOAD_MODE=%LOAD_MODE%"
if "%LOAD_MODE%"=="" set "LOAD_MODE=skip"

echo.
echo =====================================
echo POSTGRESQL DATA LOAD
echo =====================================
echo.

echo.
echo -------------------------------------
echo DETECTING SCHEMA
echo -------------------------------------
echo.

python scripts\schema_detector.py postgresql
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo GENERATING LIQUIBASE XML
echo -------------------------------------
echo.

python scripts\python\postgresql\setup\generate_liquibase_xml.py
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo UPDATING MASTER XML
echo -------------------------------------
echo.

if exist liquibase\postgresql\master.xml del /f /q liquibase\postgresql\master.xml

python scripts\python\postgresql\setup\update_master_xml.py
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo RUNNING LIQUIBASE
echo -------------------------------------
echo.

call scripts\batch\postgresql\setup\run_liquibase.bat
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo LOADING DATA
echo -------------------------------------
echo.

echo LOAD MODE : %LOAD_MODE%

set "STRICT_SCHEMA=true"

python scripts\data_loader.py postgresql
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo VALIDATING DATA
echo -------------------------------------
echo.

python scripts\python\postgresql\load\validate_data.py
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo POSTGRESQL DATA LOAD SUCCESSFUL
echo =====================================
echo.

exit /b 0
