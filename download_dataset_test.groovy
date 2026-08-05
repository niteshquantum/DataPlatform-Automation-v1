def runTrackedStage(String stageName, Closure stageBody) {

    bat """
        python scripts\\logging\\logger.py stage-start ^
        --database ${params.DATABASE} ^
        --action download-test ^
        --build-number "${env.BUILD_NUMBER}" ^
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database ${params.DATABASE} ^
            --action download-test ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status SUCCESS
        """

    } catch (Exception error) {

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database ${params.DATABASE} ^
            --action download-test ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status FAILURE
        """

        bat """
            python scripts\\logging\\logger.py set-error ^
            --database ${params.DATABASE} ^
            --action download-test ^
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
            name: 'DATABASE',
            choices: [
                'postgresql',
                'mysql',
                'mongodb',
                'mssql',
            ],
            description: 'Select target database.'
        )

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
    }

    stages {

        stage('Checkout SCM') {

            steps {

                checkout scm
            }
        }


        stage('Initialize Logging') {

            steps {

                script {

                    bat """
                        python scripts\\logging\\logger.py init ^
                        --database ${params.DATABASE} ^
                        --action download-test ^
                        --os windows ^
                        --build-number "${env.BUILD_NUMBER}" ^
                        --job-name "${env.JOB_NAME}" ^
                        --build-url "${env.BUILD_URL}"
                    """
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
                            "DATABASE=${params.DATABASE}"
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

                        bat """
                            python scripts\\python\\common\\verify_download.py ^
                            --database ${params.DATABASE} ^
                            --source-type ${params.SOURCE_TYPE} ^
                            --source-path "${params.SOURCE_PATH}"
                        """
                    }
                }
            }
        }


        stage('Extract Dataset') {

            steps {

                script {

                    runTrackedStage(
                        'Extract Dataset'
                    ) {

                        bat """
                            python scripts\\python\\common\\extract_dataset.py
                        """
                    }
                }
            }
        }


        stage('Verify Incoming Folder') {

            steps {

                script {

                    runTrackedStage(
                        'Verify Incoming Folder'
                    ) {

                        bat """
                            python scripts\\python\\common\\verify_incoming.py ^
                            --database ${params.DATABASE}
                        """
                    }
                }
            }
        }
    }


    post {

        success {

            echo 'DATASET DOWNLOAD TEST SUCCESSFUL'
        }

        failure {

            echo 'DATASET DOWNLOAD TEST FAILED'
        }

        always {

            echo 'FINALIZING DOWNLOAD TEST LOGGING'

            script {

                bat """
                    python scripts\\logging\\logger.py finalize ^
                    --database ${params.DATABASE} ^
                    --action download-test ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --status "${currentBuild.currentResult ?: 'FAILURE'}"
                """
            }
        }
    }
}