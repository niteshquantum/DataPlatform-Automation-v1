@echo off
setlocal

call "%~dp0..\common\set_project_root.bat"
if errorlevel 1 exit /b 1

cd /d "%PROJECT_ROOT%"

set "PYTHONPATH=%PROJECT_ROOT%;%PYTHONPATH%"

python -c "from scripts.python.common.config_loader import load_source_config; import pyodbc; c = load_source_config(); conn = pyodbc.connect('DRIVER={' + c['SOURCE_ODBC_DRIVER'] + '};SERVER=' + c['SOURCE_HOST'] + ',' + c['SOURCE_PORT'] + ';DATABASE=' + c['SOURCE_DB'] + ';UID=' + c['SOURCE_USER'] + ';PWD=' + c['SOURCE_PASSWORD'] + ';Encrypt=no;TrustServerCertificate=yes;Connection Timeout=30;'); cursor = conn.cursor(); cursor.execute('SELECT 1'); print('MSSQL SOURCE CONNECTION VALIDATED'); conn.close()"
if errorlevel 1 exit /b 1

exit /b 0
