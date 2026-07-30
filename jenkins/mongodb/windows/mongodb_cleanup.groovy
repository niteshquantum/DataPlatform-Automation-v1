def runTrackedStage(String stageName, Closure stageBody) {

    bat """
        python scripts\\logging\\logger.py stage-start ^
        --database mongodb ^
        --action cleanup ^
        --build-number "${env.BUILD_NUMBER}" ^
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mongodb ^
            --action cleanup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status SUCCESS
        """

    } catch (Exception error) {

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mongodb ^
            --action cleanup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status FAILURE
        """

        bat """
            python scripts\\logging\\logger.py set-error ^
            --database mongodb ^
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
            description: 'Select MongoDB cleanup mode'
        )
    }

    environment {
        PIPELINE_TYPE = "MONGODB_WINDOWS_CLEANUP"
    }


    stages {

        stage('Initialize Logging') {

            steps {

                bat """
                    python scripts\\logging\\logger.py init ^
                    --database mongodb ^
                    --action cleanup ^
                    --os windows ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --job-name "${env.JOB_NAME}" ^
                    --build-url "${env.BUILD_URL}"
                """
            }
        }


        stage('Run MongoDB Cleanup') {

            steps {

                script {

                    runTrackedStage(
                        'Run MongoDB Cleanup'
                    ) {

                        withEnv([
                            "CLEANUP_MODE=${params.CLEANUP_MODE}"
                        ]) {

                            bat 'scripts\\batch\\mongodb\\cleanup\\mongodb_cleanup_pipeline.bat'
                        }
                    }
                }
            }
        }
    }


    post {

        success {

            echo "======================================"
            echo "MONGODB WINDOWS CLEANUP SUCCESSFUL"
            echo "Cleanup Mode : ${params.CLEANUP_MODE}"
            echo "======================================"
        }


        failure {

            echo "======================================"
            echo "MONGODB WINDOWS CLEANUP FAILED"
            echo "Cleanup Mode : ${params.CLEANUP_MODE}"
            echo "======================================"
        }


        always {

            echo 'FINALIZING MONGODB CLEANUP LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult

                bat """
                    python scripts\\logging\\logger.py finalize ^
                    --database mongodb ^
                    --action cleanup ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --status "${finalStatus}"
                """

                bat """
                    python scripts\\reporting\\generate_report.py ^
                    --database mongodb ^
                    --action cleanup ^
                    --build-number "${env.BUILD_NUMBER}"
                """

                bat """
                    python scripts\\reporting\\generate_history.py ^
                    --database mongodb ^
                    --action cleanup ^
                    --build-number "${env.BUILD_NUMBER}"
                """
            }


            archiveArtifacts(
                artifacts: "logs/mongodb/cleanup/build_${env.BUILD_NUMBER}/**, reports/mongodb/cleanup/build_${env.BUILD_NUMBER}/**, reports/history/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo "Cleanup Mode: ${params.CLEANUP_MODE}"
            echo 'MONGODB CLEANUP PIPELINE COMPLETED'
        }
    }
}
