@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo        Discovering Installed JDK
echo ========================================
echo.

REM Result variables
set "JAVA_HOME="
set "SELECTED_VERSION="
set "ALL_DETECTED="

REM ----------------------------------------
REM Common installation locations
REM ----------------------------------------

for %%P in (
"C:\Program Files\Java"
"C:\Program Files\Microsoft"
"C:\Program Files\Eclipse Adoptium"
"C:\Program Files\Amazon Corretto"
) do (

    if exist "%%~P" (

        echo Checking %%~P

        for /d %%D in ("%%~P\*") do (
            set "FOLDER_NAME=%%~nxD"
            set "FOLDER_PATH=%%~fD"

            call :DetectVersion "!FOLDER_NAME!" "!FOLDER_PATH!"
        )
    )
)

echo.

REM ----------------------------------------
REM Result Check
REM ----------------------------------------

if "%SELECTED_VERSION%"=="" (
    echo ========================================
    echo ERROR: Supported JDK not found
    echo ========================================
    echo.
    echo Detected versions:
    if defined ALL_DETECTED (
        echo !ALL_DETECTED!
    ) else (
        echo   None found in standard locations
    )
    echo.
    echo Required one of: 17, 21, 22 or 25
    echo.
    echo Please install JDK 17, 21, 22 or 25 and try again.
    echo ========================================
    exit /b 1
)

REM ----------------------------------------
REM Configure Environment
REM ----------------------------------------

set "NEW_PATH=%JAVA_HOME%\bin;%PATH%"

echo ========================================
echo Java Configuration
echo ========================================
echo Selected Version : JDK %SELECTED_VERSION%
echo JAVA_HOME         : %JAVA_HOME%
echo ========================================
echo.

REM ----------------------------------------
REM Validate Installation
REM ----------------------------------------

echo Validating Java installation...
echo.

if not exist "%JAVA_HOME%\bin\java.exe" (
    echo ERROR: java.exe not found
    exit /b 1
)

if not exist "%JAVA_HOME%\bin\javac.exe" (
    echo ERROR: javac.exe not found
    echo JDK is required.
    exit /b 1
)

echo --- java -version ---
"%JAVA_HOME%\bin\java.exe" -version
if errorlevel 1 (
    echo ERROR: java validation failed
    exit /b 1
)

echo.
echo --- javac -version ---
"%JAVA_HOME%\bin\javac.exe" -version
if errorlevel 1 (
    echo ERROR: javac validation failed
    exit /b 1
)

echo.
echo ========================================
echo Java %SELECTED_VERSION% validated successfully
echo ========================================

endlocal & (
    set "JAVA_HOME=%JAVA_HOME%"
    set "PATH=%NEW_PATH%"
)

exit /b 0

REM =====================================================
REM DetectVersion
REM =====================================================
:DetectVersion

set "NAME=%~1"
set "FULL_PATH=%~2"

REM Already selected highest priority
if "%SELECTED_VERSION%"=="25" goto :EOF

set "ALL_DETECTED=!ALL_DETECTED! !NAME!"

REM ----------------------------
REM Java 25
REM ----------------------------
echo !NAME! | findstr /i "jdk-25 jdk25 -25" >nul
if not errorlevel 1 (
    set "JAVA_HOME=!FULL_PATH!"
    set "SELECTED_VERSION=25"
    echo   Found supported JDK: !NAME! ^-> selecting version 25
    goto :EOF
)

REM ----------------------------
REM Java 22
REM ----------------------------
if "%SELECTED_VERSION%"=="22" goto :EOF

echo !NAME! | findstr /i "jdk-22 jdk22 -22" >nul
if not errorlevel 1 (
    set "JAVA_HOME=!FULL_PATH!"
    set "SELECTED_VERSION=22"
    echo   Found supported JDK: !NAME! ^-> selecting version 22
    goto :EOF
)

REM ----------------------------
REM Java 21
REM ----------------------------
if "%SELECTED_VERSION%"=="21" goto :EOF

echo !NAME! | findstr /i "jdk-21 jdk21 -21" >nul
if not errorlevel 1 (
    set "JAVA_HOME=!FULL_PATH!"
    set "SELECTED_VERSION=21"
    echo   Found supported JDK: !NAME! ^-> selecting version 21
    goto :EOF
)

REM ----------------------------
REM Java 17
REM ----------------------------
if "%SELECTED_VERSION%"=="17" goto :EOF

echo !NAME! | findstr /i "jdk-17 jdk17 -17" >nul
if not errorlevel 1 (
    set "JAVA_HOME=!FULL_PATH!"
    set "SELECTED_VERSION=17"
    echo   Found supported JDK: !NAME! ^-> selecting version 17
    goto :EOF
)

echo   Ignoring unsupported: !NAME!
goto :EOF
