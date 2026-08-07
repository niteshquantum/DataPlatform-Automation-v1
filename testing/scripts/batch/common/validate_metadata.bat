@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"
if errorlevel 1 exit /b 1

cd /d "%PROJECT_ROOT%"

set "DB=%1"
if "%DB%"=="" (
    echo ERROR: Database type not provided
    exit /b 1
)

set "SCHEMA_REGISTRY=%PROJECT_ROOT%\metadata\%DB%\schema_registry.json"
set "DATATYPE_REGISTRY=%PROJECT_ROOT%\metadata\%DB%\datatype_registry.json"

echo.
echo =====================================
echo VALIDATING METADATA
echo =====================================
echo.

if not exist "%SCHEMA_REGISTRY%" (
    echo ERROR: schema_registry.json not found at %SCHEMA_REGISTRY%
    exit /b 1
)

if not exist "%DATATYPE_REGISTRY%" (
    echo ERROR: datatype_registry.json not found at %DATATYPE_REGISTRY%
    exit /b 1
)

python -c "import json; json.load(open('%SCHEMA_REGISTRY%'))" 2>nul
if errorlevel 1 (
    echo ERROR: schema_registry.json is not valid JSON
    exit /b 1
)

python -c "import json; json.load(open('%DATATYPE_REGISTRY%'))" 2>nul
if errorlevel 1 (
    echo ERROR: datatype_registry.json is not valid JSON
    exit /b 1
)

echo METADATA VALIDATION SUCCESSFUL
echo.
exit /b 0
