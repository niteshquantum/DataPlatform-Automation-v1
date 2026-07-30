pipeline {

    agent any

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

    stages {

        stage('Validate Cleanup Parameters') {

            steps {

                script {

                    if (
                        params.CLEANUP_MODE != 'PRESERVE_DATA' &&
                        params.CLEANUP_MODE != 'DELETE_DATA'
                    ) {
                        error("Invalid CLEANUP_MODE: ${params.CLEANUP_MODE}")
                    }

                    echo """
=====================================
MYSQL UBUNTU CLEANUP PARAMETERS
=====================================

Cleanup Mode : ${params.CLEANUP_MODE}
"""
                }
            }
        }

        stage('Run MySQL Cleanup') {

            steps {

                withEnv([
                    "CLEANUP_MODE=${params.CLEANUP_MODE}"
                ]) {

                    sh '''
                        echo
                        echo "====================================="
                        echo "RUNNING MYSQL UBUNTU CLEANUP"
                        echo "====================================="
                        echo

                        bash scripts/bash/mysql/cleanup/mysql_cleanup_pipeline.sh

                        echo
                        echo "====================================="
                        echo "MYSQL UBUNTU CLEANUP COMPLETED"
                        echo "====================================="
                        echo
                    '''
                }
            }
        }
    }

    post {

        success {
            echo 'MYSQL UBUNTU CLEANUP SUCCESSFUL'
        }

        failure {
            echo 'MYSQL UBUNTU CLEANUP FAILED'
        }

        always {
            echo 'MYSQL UBUNTU CLEANUP PIPELINE COMPLETED'
        }
    }
}