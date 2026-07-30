pipeline {

    agent any

    parameters {

        choice(
            name: 'CLEANUP_MODE',
            choices: [
                'PRESERVE_DATA',
                'DELETE_DATA'
            ],
            description: 'Select MongoDB cleanup mode'
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
MONGODB UBUNTU CLEANUP PARAMETERS
=====================================

Cleanup Mode : ${params.CLEANUP_MODE}
"""
                }
            }
        }

        stage('Run MongoDB Cleanup') {

            steps {

                withEnv([
                    "CLEANUP_MODE=${params.CLEANUP_MODE}"
                ]) {

                    sh '''
                        echo
                        echo "====================================="
                        echo "RUNNING MONGODB UBUNTU CLEANUP"
                        echo "====================================="
                        echo

                        bash scripts/bash/mongodb/cleanup/mongodb_cleanup_pipeline.sh

                        echo
                        echo "====================================="
                        echo "MONGODB UBUNTU CLEANUP COMPLETED"
                        echo "====================================="
                        echo
                    '''
                }
            }
        }
    }

    post {

        success {
            echo 'MONGODB UBUNTU CLEANUP SUCCESSFUL'
        }

        failure {
            echo 'MONGODB UBUNTU CLEANUP FAILED'
        }

        always {
            echo 'MONGODB UBUNTU CLEANUP PIPELINE COMPLETED'
        }
    }
}