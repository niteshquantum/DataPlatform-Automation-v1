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

        booleanParam(
            name: 'RUN_ASSESSMENT',
            defaultValue: true,
            description: 'Run database assessment after successful load.'
        )

        choice(
            name: 'SOURCE_TYPE',
            choices: [
                'google_drive',
                'local'
            ],
            description: 'Select dataset source.'
        )

        string(
            name: 'SOURCE_PATH',
            defaultValue: '',
            description: 'Dataset location (Google Drive URL or local path)'
        )

        booleanParam(
            name: 'FORCE_DOWNLOAD',
            defaultValue: false,
            description: 'Force dataset download instead of reusing an existing archive.'
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


        stage('Validate PostgreSQL Requirements') {

            steps {

                script {

                    runTrackedStage(
                        'Validate PostgreSQL Requirements'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\validate_python_requirements.bat'
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

                        bat 'scripts\\batch\\postgresql\\setup\\install_tools.bat'
                    }
                }
            }
        }


        stage('Validate Tools') {

            steps {

                script {

                    runTrackedStage(
                        'Validate Tools'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\validate_tools.bat'
                    }
                }
            }
        }


        stage('Start PostgreSQL') {

            steps {

                script {

                    runTrackedStage(
                        'Start PostgreSQL'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\start_postgresql.bat'
                    }
                }
            }
        }


        stage('Validate PostgreSQL Instance') {

            steps {

                script {

                    runTrackedStage(
                        'Validate PostgreSQL Instance'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\validate_postgresql.bat'
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
                            "FORCE_DOWNLOAD=${params.FORCE_DOWNLOAD}"
                        ]) {

                            bat 'scripts\\batch\\common\\download_dataset.bat'
                        }
                    }
                }
            }
        }

        stage('Verify Download') {

            steps {

                script {

                    runTrackedStage(
                        'Verify Download'
                    ) {

                        bat 'python scripts\\python\\common\\verify_download.py'
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

                        bat 'python scripts\\profiling\\data_profiler.py --database postgresql'
                    }
                }
            }
        }
        stage('Schema Detection') {

    steps {

        script {

            runTrackedStage('Schema Detection') {

                bat 'python scripts\\schema_detector.py postgresql'

            }

        }

    }

}

stage('Datatype Detection') {

    steps {

        script {

            runTrackedStage('Datatype Detection') {

                bat 'python scripts\\datatype_registry_generator.py postgresql'

            }

        }

    }

}

stage('Schema Editor') {

    steps {

        script {

            runTrackedStage('Schema Editor') {

                bat 'python scripts\\schema_editor\\app.py postgresql'

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

                        bat 'scripts\\batch\\postgresql\\setup\\create_database.bat'
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

                        bat 'scripts\\batch\\postgresql\\load\\validate_loaded_data.bat'
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

                        bat 'scripts\\batch\\postgresql\\objects\\deploy_objects.bat'
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

                        bat 'scripts\\batch\\postgresql\\objects\\validate_objects.bat'
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

                        bat 'scripts\\batch\\postgresql\\assessment\\run_assessment_pipeline.bat'
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

                        bat 'scripts\\batch\\postgresql\\migration\\run_migration_pipeline.bat'
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