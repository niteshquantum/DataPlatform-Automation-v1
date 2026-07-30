@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 (
    echo ERROR: PROJECT ROOT SETUP FAILED
    exit /b 1
)

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

echo.
echo -------------------------------------
echo DETECTING SCHEMA
echo -------------------------------------
echo.

python scripts\schema_detector.py mysql
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo GENERATING LIQUIBASE XML
echo -------------------------------------
echo.

python scripts\python\mysql\setup\generate_liquibase_xml.py
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo UPDATING MASTER XML
echo -------------------------------------
echo.

if exist liquibase\mysql\master.xml del /f /q liquibase\mysql\master.xml

python scripts\python\mysql\setup\update_master_xml.py
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo RUNNING LIQUIBASE
echo -------------------------------------
echo.

call scripts\batch\mysql\setup\run_liquibase.bat liquibase\mysql\master.xml
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo SCHEMA DEPLOYMENT SUCCESSFUL
echo =====================================
echo.

exit /b 0
