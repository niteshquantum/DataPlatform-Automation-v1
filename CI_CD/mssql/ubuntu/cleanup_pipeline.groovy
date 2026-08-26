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
            description: 'Select MSSQL cleanup mode'
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
MSSQL UBUNTU CLEANUP PARAMETERS
=====================================

Cleanup Mode : ${params.CLEANUP_MODE}
"""
                }
            }
        }

        stage('Run MSSQL Cleanup') {

            steps {

                withEnv([
                    "CLEANUP_MODE=${params.CLEANUP_MODE}"
                ]) {

                    sh '''
                        echo
                        echo "====================================="
                        echo "RUNNING MSSQL UBUNTU CLEANUP"
                        echo "====================================="
                        echo

                        bash scripts/bash/mssql/cleanup/mssql_cleanup_pipeline.sh

                        echo
                        echo "====================================="
                        echo "MSSQL UBUNTU CLEANUP COMPLETED"
                        echo "====================================="
                        echo
                    '''
                }
            }
        }
    }

    post {

        success {
            echo 'MSSQL UBUNTU CLEANUP SUCCESSFUL'
        }

        failure {
            echo 'MSSQL UBUNTU CLEANUP FAILED'
        }

        always {
            echo 'MSSQL UBUNTU CLEANUP PIPELINE COMPLETED'
        }
    }
}
