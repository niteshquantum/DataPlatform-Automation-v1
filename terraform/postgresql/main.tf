terraform {

  required_version = ">= 1.13.0"

  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

locals {
  project_root   = abspath("${path.module}/../..")
  powershell_dir = "${local.project_root}/scripts/powershell/postgresql"
  bash_dir       = "${local.project_root}/scripts/bash/postgresql/setup"
}

#############################################################
# WINDOWS DEPLOYMENT
#############################################################

resource "null_resource" "install_postgresql_windows" {

  provisioner "local-exec" {

    interpreter = [
      "powershell.exe",
      "-NoProfile",
      "-NonInteractive",
      "-ExecutionPolicy",
      "Bypass",
      "-File"
    ]

    command = "${local.powershell_dir}/install_windows.ps1"
  }
}

#############################################################
# LINUX DEPLOYMENT PIPELINE
#############################################################

resource "null_resource" "postgresql_install_linux" {

  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    command = "${local.bash_dir}/install_postgresql.sh"
  }
}

resource "null_resource" "postgresql_start_linux" {

  depends_on = [
    null_resource.postgresql_install_linux
  ]

  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    command = "${local.bash_dir}/start_postgresql.sh"
  }
}

resource "null_resource" "postgresql_validate_linux" {

  depends_on = [
    null_resource.postgresql_start_linux
  ]

  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    command = "${local.bash_dir}/validate_postgresql.sh"
  }
}
