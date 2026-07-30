def execute(Map context) {
    def runTrackedStage = context.runTrackedStage ?: { String stageName, Closure stageBody -> stageBody() }

    stage('Set Permissions') {
        sh '''
            find scripts/bash -type f -name "*.sh" -exec chmod +x {} \\;
        '''
    }

    stage('Validate Python Runtime') {
        runTrackedStage('Validate Python Runtime') {
            sh './scripts/bash/common/validate_python_runtime.sh'
        }
    }

    stage('Install Python Requirements') {
        runTrackedStage('Install Python Requirements') {
            sh './scripts/bash/mysql/setup/install_python_requirements.sh'
        }
    }

    stage('Validate Python Requirements') {
        runTrackedStage('Validate Python Requirements') {
            sh './scripts/bash/mysql/setup/validate_python_requirements.sh'
        }
    }

    stage('Validate Java Runtime') {
        runTrackedStage('Validate Java Runtime') {
            sh './scripts/bash/common/validate_java_runtime.sh'
        }
    }

    stage('Install Tools') {
        runTrackedStage('Install Tools') {
            sh './scripts/bash/mysql/setup/install_tools.sh'
        }
    }

    stage('Check MySQL Instance') {
        runTrackedStage('Check MySQL Instance') {
            def output = sh(
                script: 'bash scripts/bash/mysql/setup/check_instance.sh || true',
                returnStdout: true
            ).trim()

            def lines = output.split('\n')
            def state = 'UNKNOWN'

            for (int i = 0; i < lines.size(); i++) {
                def line = lines[i]

                if (line.startsWith('INSTANCE_STATE=')) {
                    state = line.split('=', 2)[1].trim()
                    break
                }
            }

            env.MYSQL_INITIAL_INSTANCE_STATE = state
            echo "Instance State: ${state}"

            if (state == 'PORT_OCCUPIED_BY_NON_MYSQL') {
                error "Port conflict: configured MySQL port is occupied by a non-MySQL process. Aborting setup."
            }

            if (state == 'UNKNOWN') {
                error "Unknown MySQL instance state detected. Aborting setup."
            }
        }
    }

    if (env.MYSQL_INITIAL_INSTANCE_STATE == 'NO_INSTANCE') {
        stage('Install MySQL') {
            runTrackedStage('Install MySQL') {
                sh './scripts/bash/mysql/setup/install_mysql.sh'
            }
        }
    }

    if (env.MYSQL_INITIAL_INSTANCE_STATE == 'NO_INSTANCE') {
        stage('Deploy MySQL') {
            runTrackedStage('Deploy MySQL') {
                sh './scripts/bash/mysql/setup/deploy_mysql.sh'
            }
        }
    }

    if (env.MYSQL_INITIAL_INSTANCE_STATE == 'INSTANCE_INSTALLED_BUT_STOPPED' || env.MYSQL_INITIAL_INSTANCE_STATE == 'NO_INSTANCE') {
        stage('Start MySQL') {
            runTrackedStage('Start MySQL') {
                sh './scripts/bash/mysql/setup/start_mysql.sh'
            }
        }
    }

    if (env.MYSQL_INITIAL_INSTANCE_STATE != 'INSTANCE_RUNNING_AND_USABLE') {
        stage('Configure Global MySQL') {
            runTrackedStage('Configure Global MySQL') {
                sh 'bash ./scripts/bash/mysql/setup/configure_global_mysql.sh'
            }
        }
    }

    stage('Configure MySQL User') {
        runTrackedStage('Configure MySQL User') {
            sh './scripts/bash/mysql/setup/configure_mysql_user.sh'
        }
    }

    // stage('Configure Database RBAC') {
    //     runTrackedStage('Configure Database RBAC') {
    //         sh './scripts/bash/mysql/setup/create_database.sh'
    //         sh './scripts/bash/mysql/rbac/configure_database_rbac.sh'
    //         sh './scripts/bash/mysql/setup/run_liquibase.sh'
    //     }
    // }

    stage('Validate Environment') {
        runTrackedStage('Validate Environment') {
            sh './scripts/bash/mysql/setup/validate_environment.sh'
        }
    }
}

return this
