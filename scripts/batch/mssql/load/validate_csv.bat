@echo off
setlocal
call "%~dp0..\..\common\set_project_root.bat"
cd /d "%PROJECT_ROOT%"
python scripts\schema_detector.py mssql || exit /b 1
python scripts\python\mssql\load\validate_csv.py
