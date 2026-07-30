@echo off
setlocal
call "%~dp0..\..\common\set_project_root.bat"
powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\powershell\mssql\cleanup\drop_mssql_database.ps1"
exit /b %errorlevel%
