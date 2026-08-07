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


def getInstanceState() {

    def output = bat(
        script: 'scripts\\batch\\mysql\\setup\\check_instance.bat',
        returnStdout: true
    ).trim()

    def state = 'UNKNOWN'

    def lines = output.split(/\r?\n/)

    for (int i = 0; i < lines.size(); i++) {

        def line = lines[i].trim()

        if (line.startsWith('INSTANCE_STATE=')) {

            state = line.split('=', 2)[1]

            break
        }
    }

    return state
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
            description: 'Dataset location (URL, local path, S3 key, etc.).'
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
                    --database mysql ^
                    --action load ^
                    --os windows ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --job-name "${env.JOB_NAME}" ^
                    --build-url "${env.BUILD_URL}"
                """

                script {
                    env.MYSQL_LOAD_LOGGING_INITIALIZED = 'true'
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


        stage('Install Python Requirements') {

            steps {

                script {

                    runTrackedStage(
                        'Install Python Requirements'
                    ) {

                        bat 'scripts\\batch\\mysql\\setup\\install_python_requirements.bat'
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

                        bat 'scripts\\batch\\mysql\\setup\\validate_python_requirements.bat'
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

                        bat 'scripts\\batch\\mysql\\setup\\install_tools.bat'
                    }
                }
            }
        }


        stage('Check MySQL Instance') {

            steps {

                script {

                    runTrackedStage(
                        'Check MySQL Instance'
                    ) {

                        def instanceState = getInstanceState()

                        echo "Instance State: ${instanceState}"
                    }
                }
            }
        }


        stage('Start MySQL Server') {

            when {

                expression {

                    def instanceState = getInstanceState()

                    return instanceState == 'INSTANCE_INSTALLED_BUT_STOPPED' || instanceState == 'NO_INSTANCE'
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Start MySQL Server'
                    ) {

                        bat 'scripts\\batch\\mysql\\setup\\start_mysql.bat'
                    }
                }
            }
        }


        stage('Validate MySQL Server') {

            steps {

                script {

                    runTrackedStage(
                        'Validate MySQL Server'
                    ) {

                        bat 'scripts\\batch\\mysql\\setup\\validate_mysql.bat'
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
                    "DATABASE=mysql"
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

                        bat 'scripts\\batch\\common\\migration\\run_data_profiling.bat mysql'
                    }
                }
            }
        }

                stage('Schema Detection') {

        steps {

            script {

                runTrackedStage('Schema Detection') {

                    bat 'python scripts\\schema_detector.py mysql'

                }

            }

        }

    }

    stage('Datatype Detection') {

        steps {

            script {

                runTrackedStage('Datatype Detection') {

                    bat 'python scripts\\datatype_registry_generator.py mysql'

                }

            }

        }

    }

    stage('Schema Editor') {

        steps {

            script {

                runTrackedStage('Schema Editor') {

                    bat 'python scripts\\schema_editor\\app.py mysql'

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


        stage('Load Data') {

            steps {

                script {

                    runTrackedStage(
                        'Load Data'
                    ) {

                        bat 'scripts\\batch\\mysql\\load\\load_data.bat'
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
                    return params.RUN_ASSESSMENT == true
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
                    return params.RUN_ASSESSMENT == true
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

                if (env.MYSQL_LOAD_LOGGING_INITIALIZED == 'true') {

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

                } else {

                    echo 'SKIPPING FINALIZE/REPORT: logging was not initialized'
                }
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
