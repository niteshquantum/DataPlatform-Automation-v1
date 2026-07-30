@echo off

echo =====================================
echo VALIDATING JAVA RUNTIME
echo =====================================

call "%~dp0discover_java.bat"
if errorlevel 1 exit /b 1

...
where java >nul 2>&1

if errorlevel 1 (
    echo ERROR: JAVA NOT FOUND IN PATH
    exit /b 1
)

echo Java Path:
where java

echo.
echo JAVA_HOME:
echo %JAVA_HOME%

echo.
echo Java Version:
java -version

if errorlevel 1 (
    echo ERROR: JAVA EXECUTION FAILED
    exit /b 1
)

echo.
echo Detecting Java Version...

for /f "tokens=3 delims= " %%i in ('java -version 2^>^&1 ^| findstr /i "version"') do (
    set JAVA_VERSION_RAW=%%i
)

set JAVA_VERSION_RAW=%JAVA_VERSION_RAW:"=%

for /f "tokens=1 delims=." %%i in ("%JAVA_VERSION_RAW%") do (
    set JAVA_MAJOR=%%i
)

if not defined JAVA_MAJOR (
    echo ERROR: UNABLE TO DETERMINE JAVA VERSION
    exit /b 1
)

echo Detected Java Major Version: %JAVA_MAJOR%

if %JAVA_MAJOR% LSS 17 (
    echo.
    echo ERROR: JAVA 17 OR HIGHER REQUIRED
    echo Detected Version: %JAVA_MAJOR%
    exit /b 1
)

if %JAVA_MAJOR% EQU 17 (
    echo.
    echo Java 17 detected - Supported
)

if %JAVA_MAJOR% GTR 17 (
    echo.
    echo Java %JAVA_MAJOR% detected - Supported
)

if %JAVA_MAJOR% EQU 21 (
    echo.
    echo Recommended Java Version Detected
)

if "%JAVA_HOME%"=="" (
    echo.
    echo WARNING: JAVA_HOME IS NOT SET
)

echo.
echo =====================================
echo JAVA RUNTIME VALIDATED
echo =====================================
echo.


exit /b 0
