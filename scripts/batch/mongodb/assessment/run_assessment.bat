@echo off
setlocal
call "%~dp0..\..\common\set_project_root.bat"
cd /d "%PROJECT_ROOT%"
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
python scripts\python\mongodb\assessment.py %*
