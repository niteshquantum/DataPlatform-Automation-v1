@echo off
setlocal

call "%~dp0set_project_root.bat"
if errorlevel 1 exit /b 1

set "SCHEMA_EDITOR_PORT="
for /f "usebackq tokens=1,* delims==" %%A in ("%PROJECT_ROOT%\config\common\network.conf") do (
    if /I "%%A"=="SCHEMA_EDITOR_PORT" set "SCHEMA_EDITOR_PORT=%%B"
)

if not defined SCHEMA_EDITOR_PORT set "SCHEMA_EDITOR_PORT=5000"

set "RULE_NAME=Schema Editor Port %SCHEMA_EDITOR_PORT% (LAN)"

echo.
echo =====================================
echo ENSURING SCHEMA EDITOR FIREWALL RULE
echo =====================================
echo.

call "%PROJECT_ROOT%\scripts\batch\common\check_admin_privileges.bat"
if errorlevel 1 (
    echo Administrator privileges not available.
    echo Schema Editor firewall rule must be created in the one-time elevated setup phase.
    exit /b 1
)

for /f "delims=" %%P in ('powershell.exe -NoProfile -NonInteractive -Command "$p = Get-NetConnectionProfile | Where-Object { $_.IPv4Connectivity -in @('Internet','LocalNetwork') } | Select-Object -First 1; if ($p) { $p.NetworkCategory } else { 'Unknown' }" 2^>nul') do set "NETWORK_CATEGORY=%%P"

if /I not "%NETWORK_CATEGORY%"=="Private" if /I not "%NETWORK_CATEGORY%"=="Domain" (
    echo WARNING: Active network profile is %NETWORK_CATEGORY%.
    echo The Schema Editor firewall rule will be created for this profile with LocalSubnet scope.
    echo For better security, consider changing the network profile to Private or Domain in Windows Settings.
)

if /I "%NETWORK_CATEGORY%"=="Private" (
    set "RULE_PROFILES=Private"
) else if /I "%NETWORK_CATEGORY%"=="Domain" (
    set "RULE_PROFILES=Domain"
) else (
    set "RULE_PROFILES=Public"
)

netsh advfirewall firewall show rule name="%RULE_NAME%" >nul 2>&1
if not errorlevel 1 (
    echo Schema Editor firewall rule already exists: %RULE_NAME%
    exit /b 0
)

netsh advfirewall firewall add rule name="%RULE_NAME%" dir=in action=allow localport=%SCHEMA_EDITOR_PORT% protocol=TCP profile=%RULE_PROFILES% remoteip=LocalSubnet >nul
if errorlevel 1 (
    echo ERROR: Failed to create the Schema Editor firewall rule for port %SCHEMA_EDITOR_PORT%.
    exit /b 1
)

echo Schema Editor firewall rule enabled: %RULE_NAME% (profile=%RULE_PROFILES%, scope=LocalSubnet)
exit /b 0
