def runTrackedStage(String stageName, Closure stageBody) {

    bat """
        python scripts\\logging\\logger.py stage-start ^
        --database postgresql ^
        --action setup ^
        --build-number "${env.BUILD_NUMBER}" ^
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database postgresql ^
            --action setup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status SUCCESS
        """

    } catch (Exception error) {

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database postgresql ^
            --action setup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status FAILURE
        """

        bat """
            python scripts\\logging\\logger.py set-error ^
            --database postgresql ^
            --action setup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --failed-stage "${stageName}" ^
            --message "Stage execution failed"
        """

        throw error
    }
}


def getInstanceState() {

    def output = bat(
        script: 'scripts\\batch\\postgresql\\setup\\check_instance.bat',
        returnStdout: true
    ).trim()

    def state = 'UNKNOWN'

    def lines = output.split('\n')

    for (int i = 0; i < lines.size(); i++) {

        def line = lines[i]

        if (line.startsWith('INSTANCE_STATE=')) {

            state = line.split('=', 2)[1]

            break
        }
    }

    return state
}


pipeline {

    agent any

    options {
        disableConcurrentBuilds()
    }

    stages {

       stage('Initialize Logging') {

            steps {

                script {

                    bat """
                        python scripts\\logging\\logger.py init ^
                        --database postgresql ^
                        --action setup ^
                        --os windows ^
                        --build-number "${env.BUILD_NUMBER}" ^
                        --job-name "${env.JOB_NAME}" ^
                        --build-url "${env.BUILD_URL}"
                    """

                    env.POSTGRESQL_SETUP_LOGGING_INITIALIZED = 'true'
                }
            }
        }


        stage('Check Administrator Privileges') {

            steps {

                script {

                    runTrackedStage(
                        'Check Administrator Privileges'
                    ) {

                        def adminStatus = bat(
                            script: 'scripts\\batch\\common\\check_admin_privileges.bat',
                            returnStatus: true
                        )

                        if (adminStatus == 0) {

                            writeFile(
                                file: 'admin_status.txt',
                                text: 'true'
                            )

                            echo 'Administrator privileges available.'
                            echo 'PostgreSQL Service and Global PSQL configuration will be enabled.'

                        } else {

                            writeFile(
                                file: 'admin_status.txt',
                                text: 'false'
                            )

                            echo 'Administrator privileges not available.'
                            echo 'PostgreSQL Service and Global PSQL configuration will be skipped.'
                            echo 'PostgreSQL will run using project-local mode.'
                        }

                        def adminResult = readFile(
                            'admin_status.txt'
                        ).trim()

                        echo "ADMIN STATUS = ${adminResult}"

                        bat """
                            python scripts\\logging\\logger.py set-environment ^
                            --database postgresql ^
                            --action setup ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --administrator-privileges "${adminResult}"
                        """
                    }
                }
            }
        }


        stage('Validate Python Runtime') {

            steps {

                script {

                    runTrackedStage(
                        'Validate Python Runtime'
                    ) {

                        bat 'scripts\\batch\\common\\validate_python_runtime.bat'
                    }
                }
            }
        }


        stage('Install Python Requirements') {

            steps {

                script {

                    runTrackedStage(
                        'Install Python Requirements'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\install_python_requirements.bat'
                    }
                }
            }
        }


        stage('Validate Python Requirements') {

            steps {

                script {

                    runTrackedStage(
                        'Validate Python Requirements'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\validate_python_requirements.bat'
                    }
                }
            }
        }


        stage('Validate Java Runtime') {

            steps {

                script {

                    runTrackedStage(
                        'Validate Java Runtime'
                    ) {

                        bat 'scripts\\batch\\common\\validate_java_runtime.bat'
                    }
                }
            }
        }


        stage('Install Tools') {

            steps {

                script {

                    runTrackedStage(
                        'Install Tools'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\install_tools.bat'
                    }
                }
            }
        }


        stage('Check PostgreSQL Instance') {

            steps {

                script {

                    runTrackedStage(
                        'Check PostgreSQL Instance'
                    ) {

                        def instanceState = getInstanceState()

                        env.POSTGRESQL_INITIAL_INSTANCE_STATE = instanceState

                        echo "Instance State: ${instanceState}"

                        if (instanceState == 'PORT_OCCUPIED_BY_NON_POSTGRESQL') {

                            error "Port conflict: configured PostgreSQL port is occupied by a non-PostgreSQL process. Aborting setup."
                        }

                        if (instanceState == 'POSTGRESQL_AUTHENTICATION_FAILED') {

                            error "PostgreSQL is reachable on the configured port, but the configured credentials were rejected. Aborting setup."
                        }

                        if (instanceState == 'UNKNOWN') {

                            error "Unknown PostgreSQL instance state detected. Aborting setup."
                        }
                    }
                }
            }
        }


        stage('Deploy PostgreSQL') {

            when {

                expression {

                    def instanceState = getInstanceState()

                    return instanceState == 'NO_INSTANCE'
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Deploy PostgreSQL'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\deploy_postgresql.bat'
                    }
                }
            }
        }


        stage('Start PostgreSQL') {

            when {

                expression {

                    def instanceState = getInstanceState()

                    return instanceState == 'INSTANCE_INSTALLED_BUT_STOPPED' || instanceState == 'NO_INSTANCE'
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Start PostgreSQL'
                    ) {

                        echo 'Starting PostgreSQL...'

                        bat 'scripts\\batch\\postgresql\\setup\\start_postgresql.bat'
                    }
                }
            }
        }


        stage('Validate PostgreSQL Instance') {

            steps {

                script {

                    runTrackedStage(
                        'Validate PostgreSQL Instance'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\validate_postgresql.bat'
                    }
                }
            }
        }


        stage('Configure PostgreSQL Service') {

            when {

                expression {

                    return readFile(
                        'admin_status.txt'
                    ).trim() == 'true'
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Configure PostgreSQL Service'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\configure_postgresql_service.bat'
                    }
                }
            }
        }


        stage('Configure Global PSQL') {

            when {

                expression {

                    return readFile(
                        'admin_status.txt'
                    ).trim() == 'true'
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Configure Global PSQL'
                    ) {

                        echo 'Administrator privileges available.'
                        echo 'Configuring Global PSQL command...'

                        bat 'scripts\\batch\\postgresql\\setup\\configure_global_psql.bat'
                    }
                }
            }
        }


        stage('Configure PostgreSQL User') {

            steps {

                script {

                    runTrackedStage(
                        'Configure PostgreSQL User'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\configure_postgresql_user.bat'
                    }
                }
            }
        }


        stage('Validate Environment') {

            steps {

                script {

                    runTrackedStage(
                        'Validate Environment'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\validate_environment.bat'
                    }
                }
            }
        }
        }


      



    post {

        success {

            echo 'POSTGRESQL SETUP SUCCESSFUL'

            script {

                def adminResult = readFile(
                    'admin_status.txt'
                ).trim()

                if (adminResult == 'true') {

                    echo 'PostgreSQL Windows Service configured successfully.'
                    echo 'Global PSQL configuration completed successfully.'

                } else {

                    echo 'PostgreSQL configured successfully in project-local mode.'
                    echo 'Windows Service and Global PSQL configuration were skipped because Administrator privileges were unavailable.'
                }
            }
        }


        failure {

            echo 'POSTGRESQL SETUP FAILED'
        }


        always {

            echo 'FINALIZING POSTGRESQL SETUP LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult ?: 'FAILURE'

                if (env.POSTGRESQL_SETUP_LOGGING_INITIALIZED == 'true') {

                    bat """
                        python scripts\\logging\\logger.py finalize ^
                        --database postgresql ^
                        --action setup ^
                        --build-number "${env.BUILD_NUMBER}" ^
                        --status "${finalStatus}"
                    """

                    bat """
                        python scripts\\reporting\\generate_report.py ^
                        --database postgresql ^
                        --action setup ^
                        --build-number "${env.BUILD_NUMBER}"
                    """

                    bat """
                        python scripts\\reporting\\generate_history.py ^
                        --database postgresql ^
                        --action setup ^
                        --build-number "${env.BUILD_NUMBER}"
                    """

                } else {

                    echo 'SKIPPING FINALIZE/REPORT: logging was not initialized'
                }
            }

            archiveArtifacts(
                artifacts: "logs/postgresql/setup/build_${env.BUILD_NUMBER}/**, reports/postgresql/setup/build_${env.BUILD_NUMBER}/**, reports/history/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo 'POSTGRESQL SETUP PIPELINE COMPLETED'
        }
    }
}
