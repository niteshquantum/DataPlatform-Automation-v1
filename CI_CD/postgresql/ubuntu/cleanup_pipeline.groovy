pipeline {

    agent {
        label 'ubuntu-node'
    }

    parameters {

        choice(
            name: 'CLEANUP_MODE',
            choices: [
                'PRESERVE_DATA',
                'DELETE_DATA',
                'RESET_SCHEMA_CONTEXT'
            ],
            description: 'Select PostgreSQL cleanup mode'
        )
    }

    stages {

        stage('Validate Cleanup Parameters') {

            steps {

                script {

                    if (
                        params.CLEANUP_MODE != 'PRESERVE_DATA' &&
                        params.CLEANUP_MODE != 'DELETE_DATA' &&
                        params.CLEANUP_MODE != 'RESET_SCHEMA_CONTEXT'
                    ) {
                        error("Invalid CLEANUP_MODE: ${params.CLEANUP_MODE}")
                    }

                    echo """
=====================================
POSTGRESQL UBUNTU CLEANUP PARAMETERS
=====================================

Cleanup Mode : ${params.CLEANUP_MODE}
"""
                }
            }
        }

        stage('Run PostgreSQL Cleanup') {

            steps {

                withEnv([
                    "CLEANUP_MODE=${params.CLEANUP_MODE}"
                ]) {

                    sh '''
                        echo
                        echo "====================================="
                        echo "RUNNING POSTGRESQL UBUNTU CLEANUP"
                        echo "====================================="
                        echo

                        bash scripts/bash/postgresql/cleanup/postgresql_cleanup_pipeline.sh

                        echo
                        echo "====================================="
                        echo "POSTGRESQL UBUNTU CLEANUP COMPLETED"
                        echo "====================================="
                        echo
                    '''
                }
            }
        }
    }

    post {

        success {
            echo 'POSTGRESQL UBUNTU CLEANUP SUCCESSFUL'
        }

        failure {
            echo 'POSTGRESQL UBUNTU CLEANUP FAILED'
        }

        always {
            echo 'POSTGRESQL UBUNTU CLEANUP PIPELINE COMPLETED'
        }
    }
}
