@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"
if errorlevel 1 exit /b 1

cd /d "%PROJECT_ROOT%"

if /I "%SCHEMA_SOURCE%"=="DATABASE" (
    python scripts\schema_extractor.py mssql
) else (
    python scripts\schema_detector.py mssql
)
if errorlevel 1 exit /b 1

exit /b 0
