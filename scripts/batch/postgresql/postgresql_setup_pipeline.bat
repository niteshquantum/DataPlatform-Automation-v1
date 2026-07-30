@echo off
setlocal

call "%~dp0..\common\set_project_root.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\common\validate_python_runtime.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\install_python_requirements.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\validate_python_requirements.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\common\validate_java_runtime.bat"
if errorlevel 1 exit /b 1

call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\install_tools.bat"
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
    echo CONFIGURING POSTGRESQL WINDOWS SERVICE
    echo =====================================
    echo.
    call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\configure_postgresql_service.bat"
    if errorlevel 1 exit /b 1

    echo.
    echo =====================================
    echo CONFIGURING GLOBAL PSQL COMMAND
    echo =====================================
    echo.
    call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\configure_global_psql.bat"
    if errorlevel 1 exit /b 1
) else (
    echo Administrator privileges not available.
    echo PostgreSQL Service and Global PSQL configuration will be skipped.
)

echo.
echo =====================================
echo CHECKING POSTGRESQL INSTANCE STATE
echo =====================================
echo.

set "INST_INSTANCE_STATE="

for /f "tokens=1* delims==" %%A in ('"%PROJECT_ROOT%\scripts\batch\postgresql\setup\check_instance.bat"') do (
    set "INST_%%A=%%B"
)

if not defined INST_INSTANCE_STATE (
    echo ERROR: Failed to determine instance state.
    exit /b 1
)

echo Instance State: %INST_INSTANCE_STATE%

if /I "%INST_INSTANCE_STATE%"=="INSTANCE_RUNNING_AND_USABLE" (
    echo Reusing existing PostgreSQL instance.
    goto :configure_user
)

if /I "%INST_INSTANCE_STATE%"=="INSTANCE_INSTALLED_BUT_STOPPED" (
    echo Starting existing PostgreSQL instance.
    call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\start_postgresql.bat"
    if errorlevel 1 exit /b 1
    goto :configure_user
)

if /I "%INST_INSTANCE_STATE%"=="NO_INSTANCE" (
    echo Deploying project-local PostgreSQL instance.
    call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\deploy_postgresql.bat"
    if errorlevel 1 exit /b 1

    echo Starting PostgreSQL instance.
    call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\start_postgresql.bat"
    if errorlevel 1 exit /b 1
    goto :configure_user
)

echo ERROR: Unexpected instance state: %INST_INSTANCE_STATE%
if defined INST_ERROR echo %INST_ERROR%
exit /b 1

:configure_user
echo.
echo =====================================
echo CONFIGURING POSTGRESQL USER
echo =====================================
echo.
call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\configure_postgresql_user.bat"
if errorlevel 1 exit /b 1

:validate_environment
call "%PROJECT_ROOT%\scripts\batch\postgresql\setup\validate_environment.bat"
if errorlevel 1 exit /b 1

echo.
echo =====================================
echo POSTGRESQL SETUP SUCCESSFUL
echo =====================================
echo.

exit /b 0