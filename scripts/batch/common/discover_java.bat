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
REM Step 1: Configuration
REM ----------------------------------------

set "SUPPORTED_VERSIONS=22 21 17"

REM Common installation locations to scan
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
REM Step 3: Result check
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
    echo Required one of: 17, 21, 22
    echo.
    echo Please install JDK 17, 21 or 22 and try again.
    echo ========================================
    exit /b 1
)

REM ----------------------------------------
REM Step 4: Set JAVA_HOME and PATH
REM ----------------------------------------

set "NEW_PATH=!JAVA_HOME!\bin;%PATH%"

echo ========================================
echo Java Configuration
echo ========================================
echo Selected Version : JDK %SELECTED_VERSION%
echo JAVA_HOME         : %JAVA_HOME%
echo ========================================
echo.

REM ----------------------------------------
REM Step 5: Validate Java installation
REM ----------------------------------------

echo Validating Java installation...
echo.

if not exist "%JAVA_HOME%\bin\java.exe" (
    echo ERROR: java.exe not found at %JAVA_HOME%\bin
    exit /b 1
)

if not exist "%JAVA_HOME%\bin\javac.exe" (
    echo ERROR: javac.exe not found at %JAVA_HOME%\bin
    echo This looks like a JRE, not a full JDK.
    exit /b 1
)

echo --- java -version ---
"%JAVA_HOME%\bin\java.exe" -version
if errorlevel 1 (
    echo ERROR: java -version failed
    exit /b 1
)

echo.
echo --- javac -version ---
"%JAVA_HOME%\bin\javac.exe" -version
if errorlevel 1 (
    echo ERROR: javac -version failed
    exit /b 1
)

echo.
echo ========================================
echo Java %SELECTED_VERSION% validated successfully
echo ========================================

REM Export variables back to caller

endlocal & (
    set "JAVA_HOME=%JAVA_HOME%"
    set "PATH=%NEW_PATH%"
)

exit /b 0


REM ============================================
REM Subroutine: DetectVersion
REM   %1 = folder name (e.g. jdk-22, jdk-11.0.31.11-hotspot)
REM   %2 = full folder path
REM ============================================
:DetectVersion
set "NAME=%~1"
set "FULL_PATH=%~2"

REM Skip if we already selected the highest priority version
if "%SELECTED_VERSION%"=="22" goto :EOF

REM Track everything we saw, for error reporting later
set "ALL_DETECTED=!ALL_DETECTED! !NAME!"

REM Check each supported version, highest priority wins.
REM Only replace an existing selection with a HIGHER version.

echo !NAME! | findstr /i "jdk-22 jdk22 -22" >nul
if not errorlevel 1 (
    set "JAVA_HOME=!FULL_PATH!"
    set "SELECTED_VERSION=22"
    echo   Found supported JDK: !NAME! -^> selecting version 22
    goto :EOF
)

if "%SELECTED_VERSION%"=="21" goto :EOF

echo !NAME! | findstr /i "jdk-21 jdk21 -21" >nul
if not errorlevel 1 (
    set "JAVA_HOME=!FULL_PATH!"
    set "SELECTED_VERSION=21"
    echo   Found supported JDK: !NAME! -^> selecting version 21
    goto :EOF
)

if "%SELECTED_VERSION%"=="17" goto :EOF

echo !NAME! | findstr /i "jdk-17 jdk17 -17" >nul
if not errorlevel 1 (
    set "JAVA_HOME=!FULL_PATH!"
    set "SELECTED_VERSION=17"
    echo   Found supported JDK: !NAME! -^> selecting version 17
    goto :EOF
)

echo   Ignoring unsupported: !NAME!
goto :EOF
