@echo off
setlocal
call "%~dp0set_project_root.bat"
cd /d "%PROJECT_ROOT%"
set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"
python scripts\python\common\assessment_report.py
