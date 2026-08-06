def runTrackedStage(String stageName, Closure stageBody) {

    bat """
        python scripts\\logging\\logger.py stage-start ^
        --database postgresql ^
        --action load ^
        --build-number "${env.BUILD_NUMBER}" ^
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database postgresql ^
            --action load ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status SUCCESS
        """

    } catch (Exception error) {

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database postgresql ^
            --action load ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status FAILURE
        """

        bat """
            python scripts\\logging\\logger.py set-error ^
            --database postgresql ^
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


    parameters {

        choice(
            name: 'SOURCE_TYPE',
            choices: [
                'google_drive',
                'local',
                's3',
                'azure_blob',
                'ftp',
                'sftp',
                'api'
            ],
            description: 'Select dataset source.'
        )

        string(
            name: 'SOURCE_PATH',
            defaultValue: '',
            description: 'Dataset location (URL, local path, folder path, etc.)'
        )

    }
    


    stages {

        stage('Initialize Logging') {

            steps {

                script {

                    bat """
                        python scripts\\logging\\logger.py init ^
                        --database postgresql ^
                        --action load ^
                        --os windows ^
                        --build-number "${env.BUILD_NUMBER}" ^
                        --job-name "${env.JOB_NAME}" ^
                        --build-url "${env.BUILD_URL}"
                    """

                    env.POSTGRESQL_LOAD_LOGGING_INITIALIZED = 'true'
                }
            }
        }


       
        stage('Download Dataset') {

            steps {

                script {

                    runTrackedStage(
                        'Download Dataset'
                    ) {

                        withEnv([
                            "SOURCE_TYPE=${params.SOURCE_TYPE}",
                            "SOURCE_PATH=${params.SOURCE_PATH}",
                            "DATABASE=postgresql"
                        ]) {

                            bat 'scripts\\batch\\common\\download_dataset.bat'
                        }
                    }
                }
            }
        }

       


    


        stage('Run CDC') {

            steps {

                script {

                    bat """
                        python scripts\\logging\\logger.py stage-start ^
                        --database postgresql ^
                        --action load ^
                        --build-number "${env.BUILD_NUMBER}" ^
                        --stage-name "Run CDC"
                    """

                    def cdcResult = bat(
                        script: 'scripts\\batch\\postgresql\\load\\run_cdc.bat',
                        returnStatus: true
                    )

                    if (cdcResult == 0 || cdcResult == 100) {
                        bat """
                            python scripts\\logging\\logger.py stage-end ^
                            --database postgresql ^
                            --action load ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --stage-name "Run CDC" ^
                            --status SUCCESS
                        """
                        if (cdcResult == 100) {
                            env.SKIP_DATA_LOAD = 'true'
                        }
                    } else {
                        bat """
                            python scripts\\logging\\logger.py stage-end ^
                            --database postgresql ^
                            --action load ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --stage-name "Run CDC" ^
                            --status FAILURE
                        """
                        bat """
                            python scripts\\logging\\logger.py set-error ^
                            --database postgresql ^
                            --action load ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --failed-stage "Run CDC" ^
                            --message "CDC execution failed with exit code ${cdcResult}"
                        """
                        error "CDC execution failed with exit code ${cdcResult}"
                    }
                }
            }
        }


        stage('Load Data') {

            when {
                expression {
                    return env.SKIP_DATA_LOAD != 'true'
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Load Data'
                    ) {

                        bat 'scripts\\batch\\postgresql\\load\\load_data.bat'
                    }
                }
            }
        }
    }

      

    post {

        success {

            echo 'POSTGRESQL LOAD SUCCESSFUL'
        }


        failure {

            echo 'POSTGRESQL LOAD FAILED'
        }


        always {

            echo 'FINALIZING POSTGRESQL LOAD LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult ?: 'FAILURE'

                if (env.POSTGRESQL_LOAD_LOGGING_INITIALIZED == 'true') {

                    bat """
                        python scripts\\logging\\logger.py finalize ^
                        --database postgresql ^
                        --action load ^
                        --build-number "${env.BUILD_NUMBER}" ^
                        --status "${finalStatus}"
                    """

                    bat """
                        python scripts\\reporting\\generate_report.py ^
                        --database postgresql ^
                        --action load ^
                        --build-number "${env.BUILD_NUMBER}"
                    """

                    bat """
                        python scripts\\reporting\\generate_history.py ^
                        --database postgresql ^
                        --action load ^
                        --build-number "${env.BUILD_NUMBER}"
                    """

                } else {

                    echo 'SKIPPING FINALIZE/REPORT: logging was not initialized'
                }
            }


            script {

                try {

                    archiveArtifacts(
                        artifacts: "logs/postgresql/load/build_${env.BUILD_NUMBER}/**, reports/postgresql/load/build_${env.BUILD_NUMBER}/**, reports/history/**, reports/migration/postgresql/**, outputs/assessments/postgresql/**, outputs/assessments/assessment_report.json, metadata/profiling/postgresql/**, metadata/reconciliation/postgresql/**, metadata/discovery/postgresql/**, metadata/assessment/postgresql/**, metadata/recommendation/postgresql/**, metadata/governance/postgresql/**",
                        fingerprint: true,
                        allowEmptyArchive: true
                    )

                } catch (Exception e) {

                    echo "Skipping archiveArtifacts: ${e.getMessage()}"
                }
            }

            echo 'POSTGRESQL LOAD PIPELINE COMPLETED'
        }
    }
}