@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"
if errorlevel 1 exit /b 1

cd /d "%PROJECT_ROOT%"
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

echo.
echo -------------------------------------
echo CDC CHECK
echo -------------------------------------
echo.

set "SCHEMA_STATUS=%PROJECT_ROOT%\metadata\mssql\schema_status.json"

if not exist "%SCHEMA_STATUS%" (
    echo SCHEMA STATUS FILE NOT FOUND: %SCHEMA_STATUS%
    echo Assuming schema changed, proceeding with full load.
    exit /b 0
)

python -c "import json; f=open(r'%SCHEMA_STATUS%','r'); d=json.load(f); f.close(); print(str(d.get('schema_changed',False)).lower())" > "%TEMP%\schema_changed.tmp"
set /p SCHEMA_CHANGED=<"%TEMP%\schema_changed.tmp"
del /f /q "%TEMP%\schema_changed.tmp"

if /I "%SCHEMA_CHANGED%"=="true" (
    echo Schema changes detected. Proceeding with full load.
    exit /b 0
)

echo No schema changes detected. Running CDC...
python scripts\cdc\cdc_engine.py mssql
set "CDC_EXIT=%ERRORLEVEL%"

if %CDC_EXIT% EQU 0 (
    echo File changes detected. Proceeding with full load.
    exit /b 0
)

if %CDC_EXIT% EQU 100 (
    echo No file changes detected. Skipping data load.
    exit /b 100
)

echo CDC execution failed with exit code %CDC_EXIT%.
exit /b %CDC_EXIT%
