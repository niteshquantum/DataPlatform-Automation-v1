@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"
if errorlevel 1 exit /b 1

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
set "LOAD_MODE=%LOAD_MODE%"
if "%LOAD_MODE%"=="" set "LOAD_MODE=skip"
set "STRICT_SCHEMA=true"

echo.
echo =====================================
echo MYSQL DATA LOAD
echo =====================================
echo.

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
echo -------------------------------------
echo LOADING DATA
echo -------------------------------------
echo.

echo LOAD MODE : %LOAD_MODE%

python scripts\data_loader.py mysql
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo VALIDATING DATA
echo -------------------------------------
echo.

python scripts\python\mysql\load\validate_data.py
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo DATA LOAD SUCCESSFUL
echo =====================================
echo.

exit /b 0
