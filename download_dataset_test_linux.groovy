def runTrackedStage(String stageName, Closure stageBody) {

    sh """
        python3 scripts/logging/logger.py stage-start \
        --database ${params.DATABASE} \
        --action download-test \
        --build-number "${env.BUILD_NUMBER}" \
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        sh """
            python3 scripts/logging/logger.py stage-end \
            --database ${params.DATABASE} \
            --action download-test \
            --build-number "${env.BUILD_NUMBER}" \
            --stage-name "${stageName}" \
            --status SUCCESS
        """

    } catch (Exception error) {

        sh """
            python3 scripts/logging/logger.py stage-end \
                --database ${params.DATABASE} \
                --action download-test \
                --build-number "${env.BUILD_NUMBER}" \
                --stage-name "${stageName}" \
                --status FAILURE
        """

        sh """
            python3 scripts/logging/logger.py set-error \
                --database ${params.DATABASE} \
                --action download-test \
                --build-number "${env.BUILD_NUMBER}" \
                --failed-stage "${stageName}" \
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


        stage('Set Permissions') {

            steps {

                sh '''
                    find scripts/bash -type f -name "*.sh" -exec chmod +x {} \\;
                '''
            }
        }


        stage('Initialize Logging') {

            steps {

                script {

                    sh """
                        python3 scripts/logging/logger.py init \
                            --database ${params.DATABASE} \
                            --action download-test \
                            --os ubuntu \
                            --build-number "${env.BUILD_NUMBER}" \
                            --job-name "${env.JOB_NAME}" \
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

                            sh './scripts/bash/common/download_dataset.sh'
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

                        withEnv([
                            "DATABASE=${params.DATABASE}",
                            "SOURCE_TYPE=${params.SOURCE_TYPE}",
                            "SOURCE_PATH=${params.SOURCE_PATH}"
                        ]) {

                            sh 'python3 scripts/python/common/verify_download.py'
                        }
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

                        withEnv([
                            "SOURCE_TYPE=${params.SOURCE_TYPE}",
                            "SOURCE_PATH=${params.SOURCE_PATH}",
                            "DATABASE=${params.DATABASE}"
                        ]) {

                            sh 'python3 scripts/python/common/extract_dataset.py'
                        }
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

                        withEnv([
                            "DATABASE=${params.DATABASE}"
                        ]) {

                            sh 'python3 scripts/python/common/verify_incoming.py'
                        }
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

                sh """
                    python3 scripts/logging/logger.py finalize \
                        --database ${params.DATABASE} \
                        --action download-test \
                        --build-number "${env.BUILD_NUMBER}" \
                        --status "${currentBuild.currentResult ?: 'FAILURE'}"
                """
            }
        }
    }
}
