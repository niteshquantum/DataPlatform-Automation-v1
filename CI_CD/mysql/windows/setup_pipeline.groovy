def runTrackedStage(String stageName, Closure stageBody) {

    bat """
        python scripts\\logging\\logger.py stage-start ^
        --database mysql ^
        --action setup ^
        --build-number "${env.BUILD_NUMBER}" ^
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mysql ^
            --action setup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status SUCCESS
        """

    } catch (Exception error) {

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mysql ^
            --action setup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status FAILURE
        """

        bat """
            python scripts\\logging\\logger.py set-error ^
            --database mysql ^
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
        script: 'scripts\\batch\\mysql\\setup\\check_instance.bat',
        returnStdout: true
    ).trim()

    def state = 'UNKNOWN'

    def lines = output.split(/\r?\n/)

    for (int i = 0; i < lines.size(); i++) {

        def line = lines[i].trim()

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
                        --database mysql ^
                        --action setup ^
                        --os windows ^
                        --build-number "${env.BUILD_NUMBER}" ^
                        --job-name "${env.JOB_NAME}" ^
                        --build-url "${env.BUILD_URL}"
                    """

                    env.MYSQL_SETUP_LOGGING_INITIALIZED = 'true'
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
                            echo 'MySQL Service and Global MySQL configuration will be enabled.'

                        } else {

                            writeFile(
                                file: 'admin_status.txt',
                                text: 'false'
                            )

                            echo 'Administrator privileges not available.'
                            echo 'MySQL Service and Global MySQL configuration will be skipped.'
                            echo 'MySQL will run using project-local mode.'
                        }

                        def adminResult = readFile(
                            'admin_status.txt'
                        ).trim()

                        echo "ADMIN STATUS = ${adminResult}"

                        bat """
                            python scripts\\logging\\logger.py set-environment ^
                            --database mysql ^
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

                        bat 'scripts\\batch\\mysql\\setup\\install_python_requirements.bat'
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

                        bat 'scripts\\batch\\mysql\\setup\\validate_python_requirements.bat'
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

                        bat 'scripts\\batch\\mysql\\setup\\install_tools.bat'
                    }
                }
            }
        }


        stage('Check MySQL Instance') {

            steps {

                script {

                    runTrackedStage(
                        'Check MySQL Instance'
                    ) {

                        def instanceState = getInstanceState()

                        env.MYSQL_INITIAL_INSTANCE_STATE = instanceState

                        echo "Instance State: ${instanceState}"

                        if (instanceState == 'PORT_OCCUPIED_BY_NON_MYSQL') {

                            error "Port conflict: configured MySQL port is occupied by a non-MySQL process. Aborting setup."
                        }

                        if (instanceState == 'UNKNOWN') {

                            error "Unknown MySQL instance state detected. Aborting setup."
                        }
                    }
                }
            }
        }


        stage('Deploy MySQL') {

            when {

                expression {
                    return env.MYSQL_INITIAL_INSTANCE_STATE == 'NO_INSTANCE'
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Deploy MySQL'
                    ) {

                        bat 'scripts\\batch\\mysql\\setup\\deploy_mysql.bat'
                    }
                }
            }
        }


        stage('Start MySQL') {

            when {

                expression {

                    def instanceState = getInstanceState()

                    return instanceState == 'INSTANCE_INSTALLED_BUT_STOPPED' || instanceState == 'NO_INSTANCE'
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Start MySQL'
                    ) {

                        echo 'Starting MySQL in project-local mode...'

                        bat 'scripts\\batch\\mysql\\setup\\start_mysql.bat'
                    }
                }
            }
        }


        stage('Validate MySQL Instance') {

            steps {

                script {

                    runTrackedStage(
                        'Validate MySQL Instance'
                    ) {

                        bat 'scripts\\batch\\mysql\\setup\\validate_mysql.bat'
                    }
                }
            }
        }


        stage('Configure MySQL Service') {

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
                        'Configure MySQL Service'
                    ) {

                        bat 'scripts\\batch\\mysql\\setup\\configure_mysql_service.bat'
                    }
                }
            }
        }


        stage('Configure Global MySQL') {

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
                        'Configure Global MySQL'
                    ) {

                        echo 'Administrator privileges available.'
                        echo 'Configuring Global MySQL command...'

                        bat 'scripts\\batch\\mysql\\setup\\configure_global_mysql.bat'
                    }
                }
            }
        }


        stage('Configure MySQL User') {

            steps {

                script {

                    runTrackedStage(
                        'Configure MySQL User'
                    ) {

                        bat 'scripts\\batch\\mysql\\setup\\configure_mysql_user.bat'
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

                        bat 'scripts\\batch\\mysql\\setup\\validate_environment.bat'
                    }
                }
            }
        }
    }


    post {

        success {

            echo 'MYSQL SETUP SUCCESSFUL'

            script {

                def adminResult = readFile(
                    'admin_status.txt'
                ).trim()

                if (adminResult == 'true') {

                    echo 'MySQL Windows Service configured successfully.'
                    echo 'Global MySQL configuration completed successfully.'

                } else {

                    echo 'MySQL configured successfully in project-local mode.'
                    echo 'Windows Service and Global MySQL configuration were skipped because Administrator privileges were unavailable.'
                }
            }
        }


        failure {

            echo 'MYSQL SETUP FAILED'
        }


        always {

            echo 'FINALIZING MYSQL SETUP LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult ?: 'FAILURE'

                if (env.MYSQL_SETUP_LOGGING_INITIALIZED == 'true') {

                    bat """
                        python scripts\\logging\\logger.py finalize ^
                        --database mysql ^
                        --action setup ^
                        --build-number "${env.BUILD_NUMBER}" ^
                        --status "${finalStatus}"
                    """

                    bat """
                        python scripts\\reporting\\generate_report.py ^
                        --database mysql ^
                        --action setup ^
                        --build-number "${env.BUILD_NUMBER}"
                    """

                    bat """
                        python scripts\\reporting\\generate_history.py ^
                        --database mysql ^
                        --action setup ^
                        --build-number "${env.BUILD_NUMBER}"
                    """

                } else {

                    echo 'SKIPPING FINALIZE/REPORT: logging was not initialized'
                }
            }


            archiveArtifacts(
                artifacts: "logs/mysql/setup/build_${env.BUILD_NUMBER}/**, reports/mysql/setup/build_${env.BUILD_NUMBER}/**, reports/history/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo 'MYSQL SETUP PIPELINE COMPLETED'
        }
    }
}
