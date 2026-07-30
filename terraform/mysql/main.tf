terraform {
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

locals {
  mysql_home = "../../databases/mysql"
}

resource "null_resource" "download_mysql_windows" {

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]

    command = <<EOT

if (!(Test-Path "..\..\databases\mysql")) {
    New-Item -ItemType Directory -Path "..\..\databases\mysql" -Force
}

$ProgressPreference = 'SilentlyContinue'

Invoke-WebRequest `
    -Uri "https://cdn.mysql.com/Downloads/MySQL-9.7/mysql-9.7.0-winx64.zip" `
    -OutFile "..\..\databases\mysql\mysql.zip" `
    -UseBasicParsing

if (!(Test-Path "..\..\databases\mysql\mysql.zip")) {
    throw "mysql.zip download failed"
}

Write-Host "Download Complete"

EOT
  }
}

resource "null_resource" "extract_mysql_windows" {

  depends_on = [null_resource.download_mysql_windows]

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]

    command = <<EOT

if (Test-Path "..\..\databases\mysql\server") {
    Remove-Item "..\..\databases\mysql\server" -Recurse -Force
}

Expand-Archive `
    -Path "..\..\databases\mysql\mysql.zip" `
    -DestinationPath "..\..\databases\mysql" `
    -Force

$folder = Get-ChildItem "..\..\databases\mysql" -Directory | Where-Object {
    $_.Name -like "mysql-*"
} | Select-Object -First 1

if ($null -eq $folder) {
    throw "MySQL extraction failed"
}

Rename-Item $folder.FullName "server" -Force

Write-Host "Extraction Complete"

EOT
  }
}

resource "null_resource" "init_mysql_windows" {

  depends_on = [null_resource.extract_mysql_windows]

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]

    command = <<EOT

if (!(Test-Path "..\..\databases\mysql\data")) {
    New-Item -ItemType Directory -Path "..\..\databases\mysql\data" -Force
}

& "..\..\databases\mysql\server\bin\mysqld.exe" `
    --initialize-insecure `
    --basedir="..\..\databases\mysql\server" `
    --datadir="..\..\databases\mysql\data"

if (!(Test-Path "..\..\databases\mysql\data\ibdata1")) {
    throw "MySQL initialization failed"
}

Write-Host "MySQL Initialized Successfully"

EOT
  }
}

resource "null_resource" "start_mysql_windows" {

  depends_on = [null_resource.init_mysql_windows]

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]

    command = "powershell -ExecutionPolicy Bypass -File ../../scripts/powershell/mysql/start_mysql.ps1"
  }
}


resource "null_resource" "create_mysql_user_windows" {

  depends_on = [null_resource.start_mysql_windows]

  triggers = {
    bootstrap_version = "config-driven-mysql-user-v2"
    config_sha        = filesha256("../../config/windows/mysql.conf")
  }

  provisioner "local-exec" {
    interpreter = ["PowerShell", "-Command"]

    command = <<EOT

$ConfigFile = "..\..\config\windows\mysql.conf"

if (!(Test-Path $ConfigFile)) {
    throw "MySQL config file not found: $ConfigFile"
}

$Config = @{}
Get-Content $ConfigFile | ForEach-Object {
    $Line = $_.Trim()
    if ($Line -and -not $Line.StartsWith("#") -and $Line.Contains("=")) {
        $Key, $Value = $Line.Split("=", 2)
        $Config[$Key.Trim()] = $Value.Trim()
    }
}

$MysqlHost = $Config["MYSQL_HOST"]
$MysqlPort = $Config["MYSQL_PORT"]
$MysqlUser = $Config["MYSQL_USER"]
$MysqlPassword = $Config["MYSQL_PASSWORD"]

if (-not $MysqlHost) { throw "MYSQL_HOST not found in mysql.conf" }
if (-not $MysqlPort) { throw "MYSQL_PORT not found in mysql.conf" }
if (-not $MysqlUser) { throw "MYSQL_USER not found in mysql.conf" }

$MysqlExe = "..\..\databases\mysql\server\bin\mysql.exe"

if (!(Test-Path $MysqlExe)) {
    throw "mysql.exe not found: $MysqlExe"
}

$RootReady = $false

for ($i = 1; $i -le 60; $i++) {
    & $MysqlExe `
      --host=$MysqlHost `
      --port=$MysqlPort `
      -u root `
      -e "SELECT 1;" 2>$null

    if ($LASTEXITCODE -eq 0) {
        $RootReady = $true
        break
    }

    Start-Sleep -Seconds 1
}

if (-not $RootReady) {
    throw "MySQL root bootstrap account is not available"
}

$EscapedUser = $MysqlUser.Replace("'", "''")
$EscapedPassword = ""

if ($MysqlPassword) {
    $EscapedPassword = $MysqlPassword.Replace("'", "''")
}

& $MysqlExe `
  --host=$MysqlHost `
  --port=$MysqlPort `
  -u root `
  -e "CREATE USER IF NOT EXISTS '$EscapedUser'@'%' IDENTIFIED BY '$EscapedPassword';
      ALTER USER '$EscapedUser'@'%' IDENTIFIED BY '$EscapedPassword';
      GRANT ALL PRIVILEGES ON *.* TO '$EscapedUser'@'%' WITH GRANT OPTION;
      CREATE USER IF NOT EXISTS '$EscapedUser'@'localhost' IDENTIFIED BY '$EscapedPassword';
      ALTER USER '$EscapedUser'@'localhost' IDENTIFIED BY '$EscapedPassword';
      GRANT ALL PRIVILEGES ON *.* TO '$EscapedUser'@'localhost' WITH GRANT OPTION;
      FLUSH PRIVILEGES;"

if ($LASTEXITCODE -ne 0) {
    throw "MySQL repository user creation failed"
}

Write-Host "MySQL repository user created successfully"

EOT
  }
}

#################################################
# LINUX (Enable during Ubuntu migration)
#################################################

# resource "null_resource" "install_mysql_linux" {
#
#   provisioner "local-exec" {
#     interpreter = ["/bin/bash", "-c"]
#     command = "../../scripts/bash/mysql/setup/install_mysql.sh"
#   }
# }
#
# resource "null_resource" "start_mysql_linux" {
#
#   depends_on = [
#     null_resource.install_mysql_linux
#   ]
#
#   provisioner "local-exec" {
#     interpreter = ["/bin/bash", "-c"]
#     command = "../../scripts/bash/mysql/setup/start_mysql.sh"
#   }
# }
