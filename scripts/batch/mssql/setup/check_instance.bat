@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

if errorlevel 1 exit /b 1

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

python "%PROJECT_ROOT%\scripts\python\mssql\setup\check_instance.py"

exit /b 0
