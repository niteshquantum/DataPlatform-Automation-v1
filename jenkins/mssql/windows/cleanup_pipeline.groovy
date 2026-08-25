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
                'DELETE_DATA',
                'RESET_SCHEMA_CONTEXT'
            ],
            description: 'Select MSSQL cleanup mode'
        )
    }

    stages {

        stage('Initialize Logging') {

            steps {

                bat """
                    python scripts\\logging\\logger.py init ^
                    --database mssql ^
                    --action cleanup ^
                    --os windows ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --job-name "${env.JOB_NAME}" ^
                    --build-url "${env.BUILD_URL}"
                """
            }
        }


        stage('Run MSSQL Cleanup') {

            steps {

                withEnv([
                    "CLEANUP_MODE=${params.CLEANUP_MODE}"
                ]) {

                    bat 'scripts\\batch\\mssql\\cleanup\\mssql_cleanup_pipeline.bat'
                }
            }
        }
    }


    post {

        success {

            echo 'MSSQL CLEANUP SUCCESSFUL'
        }


        failure {

            echo 'MSSQL CLEANUP FAILED'
        }


        always {

            echo 'FINALIZING MSSQL CLEANUP LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult ?: 'FAILURE'

                bat """
                    python scripts\\logging\\logger.py finalize ^
                    --database mssql ^
                    --action cleanup ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --status "${finalStatus}"
                """

                bat """
                    python scripts\\reporting\\generate_report.py ^
                    --database mssql ^
                    --action cleanup ^
                    --build-number "${env.BUILD_NUMBER}"
                """

                bat """
                    python scripts\\reporting\\generate_history.py ^
                    --database mssql ^
                    --action cleanup ^
                    --build-number "${env.BUILD_NUMBER}"
                """
            }


            archiveArtifacts(
                artifacts: "logs/mssql/cleanup/build_${env.BUILD_NUMBER}/**, reports/mssql/cleanup/build_${env.BUILD_NUMBER}/**, reports/history/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo "Cleanup Mode: ${params.CLEANUP_MODE}"
            echo 'MSSQL CLEANUP PIPELINE COMPLETED'
        }
    }
}
