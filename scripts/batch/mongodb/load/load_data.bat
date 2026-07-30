@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"
if errorlevel 1 exit /b 1

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

if "%LOAD_MODE%"=="" set "LOAD_MODE=skip"

echo.
echo =====================================
echo MONGODB DATA LOAD
echo =====================================
echo.

echo.
echo -------------------------------------
echo DETECTING SCHEMA
echo -------------------------------------
echo.

python scripts\schema_detector.py mongodb
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo CREATING COLLECTIONS
echo -------------------------------------
echo.

python "%PROJECT_ROOT%\scripts\python\mongodb\setup\create_collections.py"
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo VALIDATING INDEXES
echo -------------------------------------
echo.

python "%PROJECT_ROOT%\scripts\python\mongodb\setup\create_indexes.py"
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo LOADING DATA
echo -------------------------------------
echo.

echo LOAD MODE : %LOAD_MODE%

python scripts\data_loader_mongodb.py
if errorlevel 1 exit /b 1

echo.
echo -------------------------------------
echo VALIDATING DATA
echo -------------------------------------
echo.

python scripts\python\mongodb\load\validate_data.py
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo DATA LOAD SUCCESSFUL
echo =====================================
echo.

exit /b 0
