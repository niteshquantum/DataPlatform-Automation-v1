terraform {
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
  }
}

resource "null_resource" "install_mssql_driver_linux" {
  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    command = "../../scripts/bash/mssql/setup/install_mssql_driver.sh"
  }
}

resource "null_resource" "install_mssql_linux" {
  depends_on = [
    null_resource.install_mssql_driver_linux
  ]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    command = "../../scripts/bash/mssql/setup/install_mssql.sh"
  }
}

resource "null_resource" "configure_mssql_linux" {
  depends_on = [
    null_resource.install_mssql_linux
  ]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    command = "../../scripts/bash/mssql/setup/configure_mssql.sh"
  }
}

resource "null_resource" "start_mssql_linux" {
  depends_on = [
    null_resource.configure_mssql_linux
  ]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    command = "../../scripts/bash/mssql/setup/start_mssql.sh"
  }
}

resource "null_resource" "validate_mssql_linux" {
  depends_on = [
    null_resource.start_mssql_linux
  ]

  provisioner "local-exec" {
    interpreter = ["/bin/bash", "-c"]

    command = "../../scripts/bash/mssql/setup/validate_mssql.sh"
  }
}