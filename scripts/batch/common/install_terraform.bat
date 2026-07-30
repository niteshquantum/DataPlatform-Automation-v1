@echo off
setlocal

echo.
echo =====================================
echo INSTALLING TERRAFORM
echo =====================================
echo.

set "ROOT=%CD%"
set "TF_DIR=%ROOT%\tools\terraform"
set "TF_ZIP=%ROOT%\tools\terraform.zip"

if not exist "%ROOT%\tools" (
mkdir "%ROOT%\tools"
)

if not exist "%TF_DIR%" (
mkdir "%TF_DIR%"
)

if exist "%TF_DIR%\terraform.exe" (
echo Terraform already installed.
echo Skipping download...
exit /b 0
)

echo Downloading Terraform...

powershell -Command "Invoke-WebRequest -Uri 'https://releases.hashicorp.com/terraform/1.13.0/terraform_1.13.0_windows_amd64.zip' -OutFile '%TF_ZIP%'"

if errorlevel 1 (
echo ERROR: TERRAFORM DOWNLOAD FAILED
exit /b 1
)

if not exist "%TF_ZIP%" (
echo ERROR: TERRAFORM ZIP NOT FOUND
exit /b 1
)

echo Extracting Terraform...

powershell -Command "Expand-Archive '%TF_ZIP%' -DestinationPath '%TF_DIR%' -Force"

if errorlevel 1 (
echo ERROR: TERRAFORM EXTRACTION FAILED
exit /b 1
)

del "%TF_ZIP%" >nul 2>&1

if not exist "%TF_DIR%\terraform.exe" (
echo ERROR: TERRAFORM INSTALLATION VALIDATION FAILED
exit /b 1
)

echo Terraform Installed Successfully.

exit /b 0
