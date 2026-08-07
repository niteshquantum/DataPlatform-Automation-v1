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

set "BUILD_NUMBER=%2"
if "%BUILD_NUMBER%"=="" (
    echo ERROR: Build number not provided
    exit /b 1
)

set "SOURCE_DIR=%PROJECT_ROOT%\metadata\%DB%"
set "ARCHIVE_DIR=%PROJECT_ROOT%\outputs\schema_test\%DB%\build_%BUILD_NUMBER%"

echo.
echo =====================================
echo ARCHIVING METADATA
echo =====================================
echo.

if not exist "%SOURCE_DIR%\schema_registry.json" (
    echo WARNING: schema_registry.json not found, skipping archive
    goto :skip_schema
)

if not exist "%ARCHIVE_DIR%" mkdir "%ARCHIVE_DIR%"

copy /Y "%SOURCE_DIR%\schema_registry.json" "%ARCHIVE_DIR%\schema_registry.json"
copy /Y "%SOURCE_DIR%\datatype_registry.json" "%ARCHIVE_DIR%\datatype_registry.json"

:skip_schema
echo METADATA ARCHIVED TO %ARCHIVE_DIR%
echo.
exit /b 0
