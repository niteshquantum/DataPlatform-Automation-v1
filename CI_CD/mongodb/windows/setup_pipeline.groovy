def runTrackedStage(String stageName, Closure stageBody) {

    bat """
        python scripts\\logging\\logger.py stage-start ^
        --database mongodb ^
        --action setup ^
        --build-number "${env.BUILD_NUMBER}" ^
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mongodb ^
            --action setup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status SUCCESS
        """

    } catch (Exception error) {

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mongodb ^
            --action setup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status FAILURE
        """

        bat """
            python scripts\\logging\\logger.py set-error ^
            --database mongodb ^
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
        script: 'scripts\\batch\\mongodb\\setup\\check_instance.bat',
        returnStdout: true
    ).trim()

    def state = 'UNKNOWN'

    def lines = output.split('\n')

    for (int i = 0; i < lines.size(); i++) {

        def line = lines[i].replace('\r', '')

        if (line.startsWith('INSTANCE_STATE=')) {

            state = line.split('=', 2)[1].trim()

            break
        }
    }

    def allowedStates = [
        'INSTANCE_RUNNING_AND_USABLE',
        'INSTANCE_INSTALLED_BUT_STOPPED',
        'NO_INSTANCE',
        'PORT_OCCUPIED_BY_NON_MONGODB'
    ]

    if (!allowedStates.contains(state)) {

        error "Invalid MongoDB instance state detected: >${state}<"
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

                bat """
                    python scripts\\logging\\logger.py init ^
                    --database mongodb ^
                    --action setup ^
                    --os windows ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --job-name "${env.JOB_NAME}" ^
                    --build-url "${env.BUILD_URL}"
                """
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
                            echo 'Global Mongosh and MongoDB Service configuration will be enabled.'

                        } else {

                            writeFile(
                                file: 'admin_status.txt',
                                text: 'false'
                            )

                            echo 'Administrator privileges not available.'
                            echo 'Global Mongosh and MongoDB Service configuration will be skipped.'
                            echo 'MongoDB will run using project-local mode.'
                        }

                        def adminResult = readFile(
                            'admin_status.txt'
                        ).trim()

                        echo "ADMIN STATUS = ${adminResult}"

                        bat """
                            python scripts\\logging\\logger.py set-environment ^
                            --database mongodb ^
                            --action setup ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --administrator-privileges "${adminResult}"
                        """
                    }
                }
            }
        }


        // stage('Validate Python Runtime') {

        //     steps {

        //         script {

        //             runTrackedStage(
        //                 'Validate Python Runtime'
        //             ) {

        //                 bat 'scripts\\batch\\common\\validate_python_runtime.bat'
        //             }
        //         }
        //     }
        // }


        // stage('Install Python Requirements') {

        //     steps {

        //         script {

        //             runTrackedStage(
        //                 'Install Python Requirements'
        //             ) {

        //                 bat 'scripts\\batch\\mongodb\\setup\\install_python_requirements.bat'
        //             }
        //         }
        //     }
        // }


        // stage('Validate Python Requirements') {

        //     steps {

        //         script {

        //             runTrackedStage(
        //                 'Validate Python Requirements'
        //             ) {

        //                 bat 'scripts\\batch\\mongodb\\setup\\validate_python_requirements.bat'
        //             }
        //         }
        //     }
        // }


        // stage('Validate Java Runtime') {

        //     steps {

        //         script {

        //             runTrackedStage(
        //                 'Validate Java Runtime'
        //             ) {

        //                 bat 'scripts\\batch\\common\\validate_java_runtime.bat'
        //             }
        //         }
        //     }
        // }


        // stage('Install Tools') {

        //     steps {

        //         script {

        //             runTrackedStage(
        //                 'Install Tools'
        //             ) {

        //                 bat 'scripts\\batch\\mongodb\\setup\\install_tools.bat'
        //             }
        //         }
        //     }
        // }


        // stage('Validate Tools') {

        //     steps {

        //         script {

        //             runTrackedStage(
        //                 'Validate Tools'
        //             ) {

        //                 bat 'scripts\\batch\\mongodb\\setup\\validate_tools.bat'
        //             }
        //         }
        //     }
        // }


        stage('Check MongoDB Instance') {

            steps {

                script {

                    runTrackedStage(
                        'Check MongoDB Instance'
                    ) {

                        def instanceState = getInstanceState()

                        env.MONGODB_INITIAL_INSTANCE_STATE = instanceState

                        echo "Initial Instance State: >${instanceState}<"
                        echo "State length: ${instanceState.length()}"
                        echo "Deploy condition (NO_INSTANCE): ${instanceState == 'NO_INSTANCE'}"
                    }
                }
            }
        }


        stage('Deploy MongoDB') {

            when {

                expression {

                    return env.MONGODB_INITIAL_INSTANCE_STATE == 'NO_INSTANCE'
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Deploy MongoDB'
                    ) {

                        bat 'scripts\\batch\\mongodb\\setup\\run_terraform.bat'
                    }
                }
            }
        }


        stage('Configure Global Mongosh') {

            when {

                expression {

                    return (
                        readFile('admin_status.txt').trim() == 'true' &&
                        env.MONGODB_INITIAL_INSTANCE_STATE == 'NO_INSTANCE'
                    )
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Configure Global Mongosh'
                    ) {

                        echo 'Administrator privileges available.'
                        echo 'Configuring Global Mongosh command...'

                        bat 'scripts\\batch\\mongodb\\setup\\configure_global_mongosh.bat'
                    }
                }
            }
        }


        stage('Configure MongoDB Service') {

            when {

                expression {

                    return (
                        readFile('admin_status.txt').trim() == 'true' &&
                        env.MONGODB_INITIAL_INSTANCE_STATE == 'NO_INSTANCE'
                    )
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Configure MongoDB Service'
                    ) {

                        echo 'Administrator privileges available.'
                        echo 'Configuring MongoDB Windows Service...'

                        bat 'scripts\\batch\\mongodb\\setup\\configure_mongodb_service.bat'
                    }
                }
            }
        }


        stage('Start MongoDB') {

            when {

                expression {

                    return (
                        env.MONGODB_INITIAL_INSTANCE_STATE == 'INSTANCE_INSTALLED_BUT_STOPPED' ||
                        env.MONGODB_INITIAL_INSTANCE_STATE == 'NO_INSTANCE'
                    )
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Start MongoDB'
                    ) {

                        bat 'scripts\\batch\\mongodb\\setup\\start_mongodb.bat'
                    }
                }
            }
        }


        stage('Validate MongoDB Port') {

            steps {

                script {

                    runTrackedStage(
                        'Validate MongoDB Port'
                    ) {

                        bat 'scripts\\batch\\mongodb\\setup\\validate_port.bat'
                    }
                }
            }
        }


        stage('Validate MongoDB Instance') {

            steps {

                script {

                    runTrackedStage(
                        'Validate MongoDB Instance'
                    ) {

                        bat 'scripts\\batch\\mongodb\\setup\\validate_mongodb.bat'
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

                        bat 'scripts\\batch\\mongodb\\setup\\validate_environment.bat'
                    }
                }
            }
        }
    }


    post {

        success {

            echo 'MONGODB SETUP SUCCESSFUL'

            script {

                def adminResult = readFile(
                    'admin_status.txt'
                ).trim()

                if (adminResult == 'true') {

                    echo 'MongoDB Windows Service configured successfully.'
                    echo 'Global Mongosh configuration completed successfully.'

                } else {

                    echo 'MongoDB configured successfully in project-local mode.'
                    echo 'Windows Service and Global Mongosh configuration were skipped because Administrator privileges were unavailable.'
                }
            }
        }


        failure {

            echo 'MONGODB SETUP FAILED'
        }


        always {

            echo 'FINALIZING MONGODB SETUP LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult

                bat """
                    python scripts\\logging\\logger.py finalize ^
                    --database mongodb ^
                    --action setup ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --status "${finalStatus}"
                """

                bat """
                    python scripts\\reporting\\generate_report.py ^
                    --database mongodb ^
                    --action setup ^
                    --build-number "${env.BUILD_NUMBER}"
                """

                bat """
                    python scripts\\reporting\\generate_history.py ^
                    --database mongodb ^
                    --action setup ^
                    --build-number "${env.BUILD_NUMBER}"
                """
            }


            archiveArtifacts(
                artifacts: "logs/mongodb/setup/build_${env.BUILD_NUMBER}/**, reports/mongodb/setup/build_${env.BUILD_NUMBER}/**, reports/history/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo 'MONGODB SETUP PIPELINE COMPLETED'
        }
    }
}
