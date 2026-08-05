def runTrackedStage(String stageName, Closure stageBody) {

    bat """
        python scripts\\logging\\logger.py stage-start ^
        --database mssql ^
        --action load ^
        --build-number "${env.BUILD_NUMBER}" ^
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mssql ^
            --action load ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status SUCCESS
        """

    } catch (Exception error) {

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mssql ^
            --action load ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status FAILURE
        """

        bat """
            python scripts\\logging\\logger.py set-error ^
            --database mssql ^
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
            ],
            description: 'Select dataset source.'
        )

        string(
            name: 'SOURCE_PATH',
            defaultValue: '',
            description: 'Dataset location (URL, local path, folder path, etc.)'
        )

        booleanParam(
            name: 'RUN_ASSESSMENT',
            defaultValue: true,
            description: 'Run database assessment after successful load.'
        )
    }


    stages {

        stage('Initialize Logging') {

            steps {

                bat """
                    python scripts\\logging\\logger.py init ^
                    --database mssql ^
                    --action load ^
                    --os windows ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --job-name "${env.JOB_NAME}" ^
                    --build-url "${env.BUILD_URL}"
                """
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

                        bat 'scripts\\batch\\mssql\\setup\\install_python_requirements.bat'
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

                        bat 'scripts\\batch\\mssql\\setup\\validate_python_requirements.bat'
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

                        bat 'scripts\\batch\\mssql\\setup\\install_tools.bat'
                    }
                }
            }
        }


        stage('Check Instance') {

            steps {

                script {

                    bat """
                        python scripts\\logging\\logger.py stage-start ^
                        --database mssql ^
                        --action load ^
                        --build-number "${env.BUILD_NUMBER}" ^
                        --stage-name "Check Instance"
                    """

                    def output = bat(
                        script: 'scripts\\batch\\mssql\\setup\\check_instance.bat',
                        returnStdout: true
                    ).trim()

                    def instanceStateLine = output.readLines().find { line ->
                        line.startsWith('INSTANCE_STATE=')
                    }
                    def instanceState = instanceStateLine?.split('=', 2)[1]?.trim()

                    if (!instanceState) {

                        bat """
                            python scripts\\logging\\logger.py stage-end ^
                            --database mssql ^
                            --action load ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --stage-name "Check Instance" ^
                            --status FAILURE
                        """

                        bat """
                            python scripts\\logging\\logger.py set-error ^
                            --database mssql ^
                            --action load ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --failed-stage "Check Instance" ^
                            --message "Unable to determine MSSQL instance state"
                        """

                        error "Unable to determine MSSQL instance state from check_instance output"

                    }

                    if (instanceState == 'NO_INSTANCE') {

                        echo 'Deploying project-local MSSQL instance.'

                        bat 'scripts\\batch\\mssql\\setup\\deploy_mssql.bat'

                        def adminStatus = bat(
                            script: 'scripts\\batch\\common\\check_admin_privileges.bat',
                            returnStatus: true
                        )

                        if (adminStatus == 0) {

                            bat 'scripts\\batch\\mssql\\setup\\configure_mssql.bat'

                        } else {

                            echo 'Administrator privileges not available. Skipping configuration.'

                        }

                    } else if (instanceState == 'INSTANCE_INSTALLED_BUT_STOPPED') {

                        echo 'Starting existing managed MSSQL instance.'

                    } else if (instanceState == 'INSTANCE_RUNNING_AND_USABLE') {

                        echo 'Reusing existing managed MSSQL instance.'

                    } else {

                        bat """
                            python scripts\\logging\\logger.py stage-end ^
                            --database mssql ^
                            --action load ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --stage-name "Check Instance" ^
                            --status FAILURE
                        """

                        bat """
                            python scripts\\logging\\logger.py set-error ^
                            --database mssql ^
                            --action load ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --failed-stage "Check Instance" ^
                            --message "Unexpected instance state: ${instanceState}"
                        """

                        error "Unexpected MSSQL instance state: ${instanceState}"

                    }

                    bat """
                        python scripts\\logging\\logger.py stage-end ^
                        --database mssql ^
                        --action load ^
                        --build-number "${env.BUILD_NUMBER}" ^
                        --stage-name "Check Instance" ^
                        --status SUCCESS
                    """
                }
            }
        }


        stage('Start SQL Server') {

            steps {

                script {

                    runTrackedStage(
                        'Start SQL Server'
                    ) {

                        bat 'scripts\\batch\\mssql\\setup\\start_mssql.bat'
                    }
                }
            }
        }


        stage('Validate SQL Server') {

            steps {

                script {

                    runTrackedStage(
                        'Validate SQL Server'
                    ) {

                        bat 'scripts\\batch\\mssql\\setup\\validate_mssql.bat'
                    }
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
                            "DATABASE=mssql"
                        ]) {

                            bat 'scripts\\batch\\common\\download_dataset.bat'
                        }
                    }
                }
            }
        }


        stage('Profile Source Data') {

            steps {

                script {

                    runTrackedStage(
                        'Profile Source Data'
                    ) {

                        bat 'python scripts\\profiling\\data_profiler.py --database mssql'
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

                        bat 'scripts\\batch\\mssql\\setup\\create_database.bat'
                    }
                }
            }
        }


        stage('Run CDC') {

            steps {

                script {

                    bat """
                        python scripts\\logging\\logger.py stage-start ^
                        --database mssql ^
                        --action load ^
                        --build-number "${env.BUILD_NUMBER}" ^
                        --stage-name "Run CDC"
                    """

                    def cdcResult = bat(
                        script: 'scripts\\batch\\mssql\\load\\run_cdc.bat',
                        returnStatus: true
                    )

                    if (cdcResult == 0 || cdcResult == 100) {

                        bat """
                            python scripts\\logging\\logger.py stage-end ^
                            --database mssql ^
                            --action load ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --stage-name "Run CDC" ^
                            --status SUCCESS
                        """

                        if (cdcResult == 100) {

                            echo 'CDC: No changes detected — skipping data load.'
                            env.SKIP_DATA_LOAD = 'true'

                        }

                    } else {

                        bat """
                            python scripts\\logging\\logger.py stage-end ^
                            --database mssql ^
                            --action load ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --stage-name "Run CDC" ^
                            --status FAILURE
                        """

                        bat """
                            python scripts\\logging\\logger.py set-error ^
                            --database mssql ^
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

                        bat 'scripts\\batch\\mssql\\load\\load_data.bat'
                    }
                }
            }
        }


        stage('Validate Loaded Data') {

            when {
                expression {
                    return env.SKIP_DATA_LOAD != 'true'
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Validate Loaded Data'
                    ) {

                        bat 'scripts\\batch\\mssql\\load\\validate_loaded_data.bat'
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

                        bat 'scripts\\batch\\mssql\\objects\\deploy_objects.bat'
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

                        bat 'scripts\\batch\\mssql\\objects\\validate_objects.bat'
                    }
                }
            }
        }


        stage('Database Assessment') {

            when {

                expression {

                    return params.RUN_ASSESSMENT == true
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Database Assessment'
                    ) {

                        bat 'scripts\\batch\\mssql\\assessment\\run_assessment_pipeline.bat'
                    }
                }
            }
        }


        stage('Assessment Report') {

            when {

                expression {

                    return params.RUN_ASSESSMENT == true
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Assessment Report'
                    ) {

                        bat 'scripts\\batch\\mssql\\migration\\run_migration_pipeline.bat'
                    }
                }
            }
        }
    }


    post {

        success {

            echo 'MSSQL LOAD SUCCESSFUL'
        }


        failure {

            echo 'MSSQL LOAD FAILED'
        }


        always {

            echo 'FINALIZING MSSQL LOAD LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult

                bat """
                    python scripts\\logging\\logger.py finalize ^
                    --database mssql ^
                    --action load ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --status "${finalStatus}"
                """

                bat """
                    python scripts\\reporting\\generate_report.py ^
                    --database mssql ^
                    --action load ^
                    --build-number "${env.BUILD_NUMBER}"
                """

                bat """
                    python scripts\\reporting\\generate_history.py ^
                    --database mssql ^
                    --action load ^
                    --build-number "${env.BUILD_NUMBER}"
                """
            }


            archiveArtifacts(
                artifacts: "logs/mssql/load/build_${env.BUILD_NUMBER}/**, reports/mssql/load/build_${env.BUILD_NUMBER}/**, reports/history/**, reports/migration/mssql/**, outputs/assessments/mssql/**, outputs/assessments/assessment_report.json, metadata/profiling/mssql/**, metadata/reconciliation/mssql/**, metadata/discovery/mssql/**, metadata/assessment/mssql/**, metadata/recommendation/mssql/**, metadata/governance/mssql/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo 'MSSQL LOAD PIPELINE COMPLETED'
        }
    }
}
