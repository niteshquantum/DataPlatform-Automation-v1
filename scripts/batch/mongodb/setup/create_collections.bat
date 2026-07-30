@echo off
setlocal

call "%~dp0..\..\common\set_project_root.bat"

python "%PROJECT_ROOT%\scripts\python\mongodb\setup\create_collections.py"

if errorlevel 1 exit /b 1

exit /b 0