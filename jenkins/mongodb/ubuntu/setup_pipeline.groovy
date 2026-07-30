def runTrackedStage(String stageName, Closure stageBody) {

    sh """
        python3 scripts/logging/logger.py stage-start \
        --database mongodb \
        --action setup \
        --build-number "${env.BUILD_NUMBER}" \
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        sh """
            python3 scripts/logging/logger.py stage-end \
            --database mongodb \
            --action setup \
            --build-number "${env.BUILD_NUMBER}" \
            --stage-name "${stageName}" \
            --status SUCCESS
        """

    } catch (Exception error) {

        sh """
            python3 scripts/logging/logger.py stage-end \
            --database mongodb \
            --action setup \
            --build-number "${env.BUILD_NUMBER}" \
            --stage-name "${stageName}" \
            --status FAILURE
        """

        sh """
            python3 scripts/logging/logger.py set-error \
            --database mongodb \
            --action setup \
            --build-number "${env.BUILD_NUMBER}" \
            --failed-stage "${stageName}" \
            --message "Stage execution failed"
        """

        throw error
    }
}


pipeline {

    agent any

    options {
        disableConcurrentBuilds()
    }

    stages {

        stage('Initialize Logging') {

            steps {

                sh """
                    python3 scripts/logging/logger.py init \
                    --database mongodb \
                    --action setup \
                    --os ubuntu \
                    --build-number "${env.BUILD_NUMBER}" \
                    --job-name "${env.JOB_NAME}" \
                    --build-url "${env.BUILD_URL}"
                """
            }
        }


        stage('Set Permissions') {

            steps {

                script {

                    runTrackedStage('Set Permissions') {

                        sh '''
                            chmod -R +x scripts/bash
                        '''
                    }
                }
            }
        }


        stage('Validate Python Runtime') {

            steps {

                script {

                    runTrackedStage('Validate Python Runtime') {

                        sh './scripts/bash/common/validate_python_runtime.sh'
                    }
                }
            }
        }


        stage('Install Python Requirements') {

            steps {

                script {

                    runTrackedStage('Install Python Requirements') {

                        sh './scripts/bash/mongodb/setup/install_python_requirements.sh'
                    }
                }
            }
        }


        stage('Validate Python Requirements') {

            steps {

                script {

                    runTrackedStage('Validate Python Requirements') {

                        sh './scripts/bash/mongodb/setup/validate_python_requirements.sh'
                    }
                }
            }
        }


        stage('Install MongoDB') {

            steps {

                script {

                    runTrackedStage('Install MongoDB') {

                        sh './scripts/bash/mongodb/setup/install_mongodb.sh'
                    }
                }
            }
        }


        stage('Install Mongosh') {

            steps {

                script {

                    runTrackedStage('Install Mongosh') {

                        sh './scripts/bash/mongodb/setup/install_mongosh.sh'
                    }
                }
            }
        }


        stage('Configure Global Mongosh') {

            steps {

                script {

                    runTrackedStage('Configure Global Mongosh') {

                        sh './scripts/bash/mongodb/setup/configure_global_mongosh.sh'
                    }
                }
            }
        }


        stage('Start MongoDB') {

            steps {

                script {

                    runTrackedStage('Start MongoDB') {

                        sh './scripts/bash/mongodb/setup/start_mongodb.sh'
                    }
                }
            }
        }


        stage('Configure MongoDB Service') {

            steps {

                script {

                    runTrackedStage('Configure MongoDB Service') {

                        sh './scripts/bash/mongodb/setup/configure_mongodb_service.sh'
                    }
                }
            }
        }


        stage('Configure Database RBAC') {
            steps { script { runTrackedStage('Configure Database RBAC') { sh './scripts/bash/mongodb/rbac/configure_database_rbac.sh' } } }
        }

        stage('Validate MongoDB') {

            steps {

                script {

                    runTrackedStage('Validate MongoDB') {

                        sh './scripts/bash/mongodb/setup/validate_mongodb.sh'
                    }
                }
            }
        }
    }


    post {

        success {

            echo 'UBUNTU MONGODB SETUP SUCCESSFUL'
        }


        failure {

            echo 'UBUNTU MONGODB SETUP FAILED'
        }


        always {

            echo 'FINALIZING UBUNTU MONGODB SETUP LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult

                sh """
                    python3 scripts/logging/logger.py finalize \
                    --database mongodb \
                    --action setup \
                    --build-number "${env.BUILD_NUMBER}" \
                    --status "${finalStatus}"
                """

                sh """
                    python3 scripts/reporting/generate_report.py \
                    --database mongodb \
                    --action setup \
                    --build-number "${env.BUILD_NUMBER}"
                """

                sh """
                    python3 scripts/reporting/generate_history.py \
                    --database mongodb \
                    --action setup \
                    --build-number "${env.BUILD_NUMBER}"
                """
            }


            archiveArtifacts(
                artifacts: "logs/mongodb/setup/build_${env.BUILD_NUMBER}/**, reports/mongodb/setup/build_${env.BUILD_NUMBER}/**, reports/history/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo 'UBUNTU MONGODB SETUP PIPELINE COMPLETED'
        }
    }
}
