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
            name: 'SCHEMA_SOURCE',
            choices: [
                'CSV',
                'DATABASE'
            ],
            defaultValue: 'CSV',
            description: 'Schema detection source'
        )

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
                    env.SCHEMA_SOURCE = params.SCHEMA_SOURCE
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
