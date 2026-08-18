@echo off
setlocal

call "%~dp0..\common\set_project_root.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\common\validate_python_runtime.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\mysql\setup\install_python_requirements.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\mysql\setup\validate_python_requirements.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\common\validate_java_runtime.bat"
if errorlevel 1 exit /b 1 

call "%PROJECT_ROOT%\scripts\batch\mysql\setup\install_tools.bat"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo CHECKING ADMINISTRATOR PRIVILEGES
echo =====================================
echo.

set "ADMIN_STATUS="

call "%PROJECT_ROOT%\scripts\batch\common\check_admin_privileges.bat"
if errorlevel 1 (
    set "ADMIN_STATUS=false"
) else (
    set "ADMIN_STATUS=true"
)

echo Administrator Status: %ADMIN_STATUS%

if /I "%ADMIN_STATUS%"=="true" (
    echo.
    echo =====================================
    echo ENSURING SCHEMA EDITOR FIREWALL ACCESS
    echo =====================================
    echo.
    call "%PROJECT_ROOT%\scripts\batch\common\ensure_schema_editor_firewall.bat"
    if errorlevel 1 exit /b 1

    echo.
    echo =====================================
    echo CONFIGURING MYSQL WINDOWS SERVICE
    echo =====================================
    echo.
    call "%PROJECT_ROOT%\scripts\batch\mysql\setup\configure_mysql_service.bat"
    if errorlevel 1 exit /b 1

    echo.
    echo =====================================
    echo CONFIGURING GLOBAL MYSQL COMMAND
    echo =====================================
    echo.
    call "%PROJECT_ROOT%\scripts\batch\mysql\setup\configure_global_mysql.bat"
    if errorlevel 1 exit /b 1
) else (
    echo Administrator privileges not available.
    echo MySQL Service and Global MySQL configuration will be skipped.
)

echo.
echo =====================================
echo CHECKING MYSQL INSTANCE STATE
echo =====================================
echo.

set "INST_INSTANCE_STATE="

for /f "tokens=1* delims==" %%A in ('"%PROJECT_ROOT%\scripts\batch\mysql\setup\check_instance.bat"') do (
    set "INST_%%A=%%B"
)

if not defined INST_INSTANCE_STATE (
    echo ERROR: Failed to determine instance state.
    exit /b 1
)

echo Instance State: %INST_INSTANCE_STATE%

if /I "%INST_INSTANCE_STATE%"=="INSTANCE_RUNNING_AND_USABLE" (
    echo Reusing existing MySQL instance.
    goto :validate_instance
)

if /I "%INST_INSTANCE_STATE%"=="INSTANCE_INSTALLED_BUT_STOPPED" (
    echo Starting existing project-local MySQL instance.
    call "%PROJECT_ROOT%\scripts\batch\mysql\setup\start_mysql.bat"
    if errorlevel 1 exit /b 1
    goto :validate_instance
)

if /I "%INST_INSTANCE_STATE%"=="NO_INSTANCE" (
    echo Deploying project-local MySQL instance.
    call "%PROJECT_ROOT%\scripts\batch\mysql\setup\deploy_mysql.bat"
    if errorlevel 1 exit /b 1

    echo Starting MySQL instance.
    call "%PROJECT_ROOT%\scripts\batch\mysql\setup\start_mysql.bat"
    if errorlevel 1 exit /b 1
    goto :validate_instance
)

echo ERROR: Unexpected instance state: %INST_INSTANCE_STATE%
if defined INST_ERROR echo %INST_ERROR%
exit /b 1

:validate_instance
call "%PROJECT_ROOT%\scripts\batch\mysql\setup\validate_mysql.bat"
if errorlevel 1 exit /b 1

@REM Database creation is LOAD responsibility.
@REM call "%PROJECT_ROOT%\scripts\batch\mysql\setup\create_database.bat"
@REM if errorlevel 1 exit /b 1

@REM call "%PROJECT_ROOT%\scripts\batch\mysql\setup\configure_global_mysql.bat"
@REM if errorlevel 1 exit /b 1

echo.
echo =====================================
echo CONFIGURING MYSQL USER
echo =====================================
echo.
call "%PROJECT_ROOT%\scripts\batch\mysql\setup\configure_mysql_user.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\mysql\setup\validate_environment.bat"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo MYSQL SETUP SUCCESSFUL
echo =====================================
echo.

exit /b 0
