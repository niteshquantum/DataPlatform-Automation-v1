def runTrackedStage(String stageName, Closure stageBody) {

    bat """
        python scripts\\logging\\logger.py stage-start ^
        --database mysql ^
        --action cleanup ^
        --build-number "${env.BUILD_NUMBER}" ^
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mysql ^
            --action cleanup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status SUCCESS
        """

    } catch (Exception error) {

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mysql ^
            --action cleanup ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status FAILURE
        """

        bat """
            python scripts\\logging\\logger.py set-error ^
            --database mysql ^
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
            description: 'Select MySQL cleanup mode'
        )
    }

    environment {
        PIPELINE_TYPE = "MYSQL_WINDOWS_CLEANUP"
    }


    stages {

        stage('Initialize Logging') {

            steps {

                bat """
                    python scripts\\logging\\logger.py init ^
                    --database mysql ^
                    --action cleanup ^
                    --os windows ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --job-name "${env.JOB_NAME}" ^
                    --build-url "${env.BUILD_URL}"
                """
            }
        }


        stage('Cleanup MySQL') {

            steps {

                script {

                    runTrackedStage(
                        'Cleanup MySQL'
                    ) {

                        withEnv([
                            "CLEANUP_MODE=${params.CLEANUP_MODE}"
                        ]) {

                            bat 'scripts\\batch\\mysql\\cleanup\\cleanup_mysql.bat'
                        }
                    }
                }
            }
        }
    }


    post {

        success {

            echo "====================================="
            echo "MYSQL WINDOWS CLEANUP PIPELINE SUCCESSFUL"
            echo "====================================="
        }


        failure {

            echo "====================================="
            echo "MYSQL WINDOWS CLEANUP PIPELINE FAILED"
            echo "====================================="
        }


        always {

            echo 'FINALIZING MYSQL CLEANUP LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult

                bat """
                    python scripts\\logging\\logger.py finalize ^
                    --database mysql ^
                    --action cleanup ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --status "${finalStatus}"
                """

                bat """
                    python scripts\\reporting\\generate_report.py ^
                    --database mysql ^
                    --action cleanup ^
                    --build-number "${env.BUILD_NUMBER}"
                """

                bat """
                    python scripts\\reporting\\generate_history.py ^
                    --database mysql ^
                    --action cleanup ^
                    --build-number "${env.BUILD_NUMBER}"
                """
            }


            archiveArtifacts(
                artifacts: "logs/mysql/cleanup/build_${env.BUILD_NUMBER}/**, reports/mysql/cleanup/build_${env.BUILD_NUMBER}/**, reports/history/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo "Cleanup Mode: ${params.CLEANUP_MODE}"
            echo 'MYSQL CLEANUP PIPELINE COMPLETED'
        }
    }
}
