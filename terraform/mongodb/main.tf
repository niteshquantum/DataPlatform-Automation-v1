terraform {
  required_version = ">= 1.5"

  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

#################################################
# WINDOWS
#################################################

resource "null_resource" "download_mongodb_windows" {

  triggers = {
    download_script_sha256 = filesha256("${path.module}/../../scripts/powershell/mongodb/setup/download_mongodb.ps1")
    mongodb_url            = "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-8.0.12.zip"
    mongodb_port           = var.mongodb_port
  }

  provisioner "local-exec" {

    interpreter = ["PowerShell", "-ExecutionPolicy", "Bypass", "-File"]

    command = "${path.module}/../../scripts/powershell/mongodb/setup/download_mongodb.ps1"

    environment = {
      DOWNLOAD_URL       = "https://fastdl.mongodb.org/windows/mongodb-windows-x86_64-8.0.12.zip"
      DOWNLOAD_OUTPUT_PATH = "${path.module}/../../databases/mongodb/mongodb.zip"
    }
  }
}

resource "null_resource" "extract_mongodb_windows" {

  depends_on = [
    null_resource.download_mongodb_windows
  ]

  provisioner "local-exec" {

    interpreter = ["PowerShell", "-Command"]

    command = <<EOT

$ErrorActionPreference = 'Stop'

$ZipPath = "..\..\databases\mongodb\mongodb.zip"
$ValidationPath = Join-Path ([System.IO.Path]::GetTempPath()) "mongodb-zip-validation-$PID"

try {
    if (Test-Path -LiteralPath $ValidationPath) {
        Remove-Item -LiteralPath $ValidationPath -Recurse -Force
    }

    Expand-Archive -LiteralPath $ZipPath -DestinationPath $ValidationPath -Force
    Remove-Item -LiteralPath $ValidationPath -Recurse -Force
}
catch {
    if (Test-Path -LiteralPath $ValidationPath) {
        Remove-Item -LiteralPath $ValidationPath -Recurse -Force -ErrorAction SilentlyContinue
    }

    throw "Invalid/corrupt MongoDB archive detected: $ZipPath"
}

if (Test-Path "..\..\databases\mongodb\server") {
    Remove-Item "..\..\databases\mongodb\server" -Recurse -Force
}

Expand-Archive `
    -Path "..\..\databases\mongodb\mongodb.zip" `
    -DestinationPath "..\..\databases\mongodb" `
    -Force

$folder = Get-ChildItem "..\..\databases\mongodb" -Directory |
Where-Object { $_.Name -like "mongodb-*" } |
Select-Object -First 1

if ($null -eq $folder) {
    throw "MongoDB extraction failed"
}

Rename-Item $folder.FullName "server" -Force

Write-Host "MongoDB Extraction Complete"

EOT

  }
}

resource "null_resource" "download_mongosh_windows" {

  depends_on = [
    null_resource.extract_mongodb_windows
  ]

  triggers = {
    download_script_sha256 = filesha256("${path.module}/../../scripts/powershell/mongodb/setup/download_mongodb.ps1")
    mongosh_url            = "https://downloads.mongodb.com/compass/mongosh-2.5.8-win32-x64.zip"
    mongodb_port           = var.mongodb_port
  }

  provisioner "local-exec" {

    interpreter = ["PowerShell", "-ExecutionPolicy", "Bypass", "-File"]

    command = "${path.module}/../../scripts/powershell/mongodb/setup/download_mongodb.ps1"

    environment = {
      DOWNLOAD_URL       = "https://downloads.mongodb.com/compass/mongosh-2.5.8-win32-x64.zip"
      DOWNLOAD_OUTPUT_PATH = "${path.module}/../../databases/mongodb/mongosh.zip"
    }
  }
}

resource "null_resource" "extract_mongosh_windows" {

  depends_on = [
    null_resource.download_mongosh_windows
  ]

  provisioner "local-exec" {

    interpreter = ["PowerShell", "-Command"]

    command = <<EOT

$ErrorActionPreference = 'Stop'

$ZipPath = "..\..\databases\mongodb\mongosh.zip"
$ValidationPath = Join-Path ([System.IO.Path]::GetTempPath()) "mongosh-zip-validation-$PID"

try {
    if (Test-Path -LiteralPath $ValidationPath) {
        Remove-Item -LiteralPath $ValidationPath -Recurse -Force
    }

    Expand-Archive -LiteralPath $ZipPath -DestinationPath $ValidationPath -Force
    Remove-Item -LiteralPath $ValidationPath -Recurse -Force
}
catch {
    if (Test-Path -LiteralPath $ValidationPath) {
        Remove-Item -LiteralPath $ValidationPath -Recurse -Force -ErrorAction SilentlyContinue
    }

    throw "Invalid/corrupt mongosh archive detected: $ZipPath"
}

if (Test-Path "..\..\databases\mongodb\mongosh") {
    Remove-Item "..\..\databases\mongodb\mongosh" -Recurse -Force
}

Expand-Archive `
    -Path "..\..\databases\mongodb\mongosh.zip" `
    -DestinationPath "..\..\databases\mongodb" `
    -Force

$folder = Get-ChildItem "..\..\databases\mongodb" -Directory |
Where-Object { $_.Name -like "mongosh-*" } |
Select-Object -First 1

Rename-Item $folder.FullName "mongosh" -Force

Write-Host "mongosh Extraction Complete"

EOT

  }
}

resource "null_resource" "initialize_mongodb_windows" {

  depends_on = [
    null_resource.extract_mongosh_windows
  ]

  provisioner "local-exec" {

    interpreter = ["PowerShell", "-Command"]

    command = <<EOT

if (!(Test-Path "..\..\databases\mongodb\data")) {
    New-Item -ItemType Directory -Path "..\..\databases\mongodb\data" -Force
}

if (!(Test-Path "..\..\databases\mongodb\logs")) {
    New-Item -ItemType Directory -Path "..\..\databases\mongodb\logs" -Force
}

if (!(Test-Path "..\..\databases\mongodb\config")) {
    New-Item -ItemType Directory -Path "..\..\databases\mongodb\config" -Force
}

Write-Host "MongoDB directories created successfully"

EOT

  }
}

resource "null_resource" "configure_mongodb_windows" {

  depends_on = [
    null_resource.initialize_mongodb_windows
  ]

  triggers = {
    mongodb_version      = "8.0.12"
    script_version       = "2.3"
    mongodb_port         = var.mongodb_port
    use_existing_mongodb = tostring(var.use_existing_mongodb)
  }

  provisioner "local-exec" {

    environment = {
      MONGODB_PORT         = tostring(var.mongodb_port)
      USE_EXISTING_MONGODB = tostring(var.use_existing_mongodb)
    }

    interpreter = [
      "PowerShell",
      "-ExecutionPolicy",
      "Bypass",
      "-File"
    ]

    command = "${path.module}/../../scripts/powershell/mongodb/install_windows.ps1"
  }
}

#################################################
# LINUX (Enable during Ubuntu migration)
#################################################

# resource "null_resource" "install_mongodb_linux" {
#
#   provisioner "local-exec" {
#     interpreter = ["/bin/bash", "-c"]
#     command = "../../scripts/bash/mongodb/setup/install_mongodb.sh"
#   }
# }
#
# resource "null_resource" "start_mongodb_linux" {
#
#   depends_on = [
#     null_resource.install_mongodb_linux
#   ]
#
#   provisioner "local-exec" {
#     interpreter = ["/bin/bash", "-c"]
#     command = "../../scripts/bash/mongodb/setup/start_mongodb.sh"
#   }
# }
