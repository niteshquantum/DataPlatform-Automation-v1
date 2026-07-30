def runTrackedStage(String stageName, Closure stageBody) {

    bat """
        python scripts\\logging\\logger.py stage-start ^
        --database mysql ^
        --action load ^
        --build-number "${env.BUILD_NUMBER}" ^
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mysql ^
            --action load ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status SUCCESS
        """

    } catch (Exception error) {

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mysql ^
            --action load ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status FAILURE
        """

        bat """
            python scripts\\logging\\logger.py set-error ^
            --database mysql ^
            --action load ^
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


    stages {

        stage('Initialize Logging') {

            steps {

                bat """
                    python scripts\\logging\\logger.py init ^
                    --database mysql ^
                    --action load ^
                    --os windows ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --job-name "${env.JOB_NAME}" ^
                    --build-url "${env.BUILD_URL}"
                """
            }
        }


        stage('Download Dataset') {

            steps {

                script {

                    runTrackedStage(
                        'Download Dataset'
                    ) {

                        bat 'scripts\\batch\\common\\download_dataset.bat'
                    }
                }
            }
        }


        stage('Create Database') {

            steps {

                script {

                    runTrackedStage(
                        'Create Database'
                    ) {

                        bat 'scripts\\batch\\mysql\\setup\\create_database.bat'
                    }
                }
            }
        }


        stage('Validate Database') {

            steps {

                script {

                    runTrackedStage(
                        'Validate Database'
                    ) {

                        bat 'scripts\\batch\\mysql\\load\\validate_database.bat'
                    }
                }
            }
        }


        stage('Deploy Schema') {

            steps {

                script {

                    runTrackedStage(
                        'Deploy Schema'
                    ) {

                        bat 'scripts\\batch\\mysql\\load\\deploy_schema.bat'
                    }
                }
            }
        }


        stage('Validate Schema') {

            steps {

                script {

                    runTrackedStage(
                        'Validate Schema'
                    ) {

                        bat 'scripts\\batch\\mysql\\load\\validate_schema.bat'
                    }
                }
            }
        }


        stage('Run CDC') {

            steps {

                script {

                    runTrackedStage(
                        'Run CDC'
                    ) {

                        bat 'scripts\\batch\\mysql\\load\\run_cdc.bat'
                    }
                }
            }
        }


        stage('Validate Source Data') {

            steps {

                script {

                    runTrackedStage(
                        'Validate Source Data'
                    ) {

                        bat 'scripts\\batch\\mysql\\load\\validate_source.bat'
                    }
                }
            }
        }


        stage('Load Data') {

            steps {

                script {

                    runTrackedStage(
                        'Load Data'
                    ) {

                        bat 'scripts\\batch\\mysql\\load\\load_data_strict.bat'
                    }
                }
            }
        }


        stage('Validate Loaded Data') {

            steps {

                script {

                    runTrackedStage(
                        'Validate Loaded Data'
                    ) {

                        bat 'scripts\\batch\\mysql\\load\\validate_loaded_data.bat'
                    }
                }
            }
        }


        stage('Deploy Database Objects') {

            steps {

                script {

                    runTrackedStage(
                        'Deploy Database Objects'
                    ) {

                        bat 'scripts\\batch\\mysql\\objects\\deploy_objects.bat'
                    }
                }
            }
        }


        stage('Validate Database Objects') {

            steps {

                script {

                    runTrackedStage(
                        'Validate Database Objects'
                    ) {

                        bat 'scripts\\batch\\mysql\\objects\\validate_objects.bat'
                    }
                }
            }
        }


        /*
        ============================================================
        OPTIONAL POST-PROCESSING
        Assessment/reporting is intentionally not part of CORE LOAD.
        Execute through dedicated assessment/reporting entry point.
        ============================================================
        */


        stage('Database Assessment') {

            when {

                expression {
                    return params.RUN_ASSESSMENT == 'true'
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Database Assessment'
                    ) {

                        bat 'scripts\\batch\\mysql\\assessment\\run_assessment.bat all'
                    }
                }
            }
        }


        stage('Assessment Report') {

            when {

                expression {
                    return params.RUN_ASSESSMENT == 'true'
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Assessment Report'
                    ) {

                        bat 'scripts\\batch\\common\\generate_assessment_report.bat'
                    }
                }
            }
        }
    }


    post {

        success {

            echo 'MYSQL LOAD SUCCESSFUL'
        }


        failure {

            echo 'MYSQL LOAD FAILED'
        }


        always {

            echo 'FINALIZING MYSQL LOAD LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult

                bat """
                    python scripts\\logging\\logger.py finalize ^
                    --database mysql ^
                    --action load ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --status "${finalStatus}"
                """

                bat """
                    python scripts\\reporting\\generate_report.py ^
                    --database mysql ^
                    --action load ^
                    --build-number "${env.BUILD_NUMBER}"
                """

                bat """
                    python scripts\\reporting\\generate_history.py ^
                    --database mysql ^
                    --action load ^
                    --build-number "${env.BUILD_NUMBER}"
                """
            }


            archiveArtifacts(
                artifacts: "logs/mysql/load/build_${env.BUILD_NUMBER}/**, reports/mysql/load/build_${env.BUILD_NUMBER}/**, reports/history/**, reports/migration/mysql/**, outputs/assessments/mysql/**, outputs/assessments/assessment_report.json, metadata/profiling/mysql/**, metadata/reconciliation/mysql/**, metadata/discovery/mysql/**, metadata/assessment/mysql/**, metadata/recommendation/mysql/**, metadata/governance/mysql/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo 'MYSQL LOAD PIPELINE COMPLETED'
        }
    }
}
