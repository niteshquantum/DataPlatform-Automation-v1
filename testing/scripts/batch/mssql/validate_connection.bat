@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"
if errorlevel 1 exit /b 1

cd /d "%PROJECT_ROOT%"

python scripts\batch\mssql\setup\validate_mssql.bat
if errorlevel 1 exit /b 1

exit /b 0
