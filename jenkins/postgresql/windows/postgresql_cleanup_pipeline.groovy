def runTrackedStage(String stageName, Closure stageBody) {

    bat """
        python scripts\\logging\\logger.py stage-start ^
        --database postgresql ^
        --action cleanup ^
        --build-number "${env.BUILD_NUMBER}" ^
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database postgresql ^
            --action cleanup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status SUCCESS
        """

    } catch (Exception error) {

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database postgresql ^
            --action cleanup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status FAILURE
        """

        bat """
            python scripts\\logging\\logger.py set-error ^
            --database postgresql ^
            --action cleanup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --failed-stage "${stageName}" ^
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


    parameters {

        choice(
            name: 'CLEANUP_MODE',
            choices: [
                'PRESERVE_DATA',
                'DELETE_DATA'
            ],
            description: 'Select PostgreSQL cleanup mode'
        )
    }

    environment {
        PIPELINE_TYPE = "POSTGRESQL_WINDOWS_CLEANUP"
    }


    stages {

        stage('Initialize Logging') {

            steps {

                bat """
                    python scripts\\logging\\logger.py init ^
                    --database postgresql ^
                    --action cleanup ^
                    --os windows ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --job-name "${env.JOB_NAME}" ^
                    --build-url "${env.BUILD_URL}"
                """
            }
        }


        stage('Cleanup PostgreSQL') {

            steps {

                script {

                    runTrackedStage(
                        'Cleanup PostgreSQL'
                    ) {

                        withEnv([
                            "CLEANUP_MODE=${params.CLEANUP_MODE}"
                        ]) {

                            bat 'scripts\\batch\\postgresql\\cleanup\\postgresql_cleanup_pipeline.bat'
                        }
                    }
                }
            }
        }
    }


    post {

        success {

            echo "====================================="
            echo "POSTGRESQL WINDOWS CLEANUP PIPELINE SUCCESSFUL"
            echo "====================================="
        }


        failure {

            echo "====================================="
            echo "POSTGRESQL WINDOWS CLEANUP PIPELINE FAILED"
            echo "====================================="
        }


        always {

            echo 'FINALIZING POSTGRESQL CLEANUP LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult

                bat """
                    python scripts\\logging\\logger.py finalize ^
                    --database postgresql ^
                    --action cleanup ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --status "${finalStatus}"
                """

                bat """
                    python scripts\\reporting\\generate_report.py ^
                    --database postgresql ^
                    --action cleanup ^
                    --build-number "${env.BUILD_NUMBER}"
                """

                bat """
                    python scripts\\reporting\\generate_history.py ^
                    --database postgresql ^
                    --action cleanup ^
                    --build-number "${env.BUILD_NUMBER}"
                """
            }


            archiveArtifacts(
                artifacts: "logs/postgresql/cleanup/build_${env.BUILD_NUMBER}/**, reports/postgresql/cleanup/build_${env.BUILD_NUMBER}/**, reports/history/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo "Cleanup Mode: ${params.CLEANUP_MODE}"
            echo 'POSTGRESQL CLEANUP PIPELINE COMPLETED'
        }
    }
}
