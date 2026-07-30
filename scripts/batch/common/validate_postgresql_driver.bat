@echo off
setlocal

call "%~dp0set_project_root.bat"
if errorlevel 1 exit /b 1

dir /b "%PROJECT_ROOT%\tools\drivers\postgresql-*.jar" >nul 2>&1

if errorlevel 1 (
    echo PostgreSQL JDBC Driver not found
    exit /b 1
)

echo PostgreSQL JDBC Driver validated

exit /b 0