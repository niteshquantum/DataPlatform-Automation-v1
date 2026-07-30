@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
set "LOAD_MODE=%LOAD_MODE%"
if "%LOAD_MODE%"=="" set "LOAD_MODE=skip"

echo.
echo =====================================
echo MSSQL DATA LOAD
echo =====================================
echo.

echo.
echo -------------------------------------
echo DETECTING SCHEMA
echo -------------------------------------
echo.

python scripts\schema_detector.py mssql
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo GENERATING LIQUIBASE XML
echo -------------------------------------
echo.

python scripts\python\mssql\setup\generate_liquibase_xml.py
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo UPDATING MASTER XML
echo -------------------------------------
echo.

if exist liquibase\mssql\master.xml del /f /q liquibase\mssql\master.xml

python scripts\python\mssql\setup\update_master_xml.py
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo RUNNING LIQUIBASE
echo -------------------------------------
echo.

call scripts\batch\mssql\setup\run_liquibase.bat
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo LOADING DATA
echo -------------------------------------
echo.

echo LOAD MODE : %LOAD_MODE%

set "STRICT_SCHEMA=true"

python scripts\data_loader.py mssql
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo VALIDATING DATA
echo -------------------------------------
echo.

python scripts\python\mssql\load\validate_data.py
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo DATA LOAD SUCCESSFUL
echo =====================================
echo.

exit /b 0