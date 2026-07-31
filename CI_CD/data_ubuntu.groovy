pipeline {

    agent {
        label 'ubuntu-node'
    }

    options {
        disableConcurrentBuilds()
    }

    stages {

        stage('Set Permissions') {

            steps {

                sh '''
                    find scripts/bash -type f -name "*.sh" -exec chmod +x {} \\;
                '''
            }
        }

        stage('Install Python Requirements') {

            steps {

                sh './scripts/bash/postgresql/setup/install_python_requirements.sh'
            }
        }

        stage('Download Dataset') {

            steps {

                sh './scripts/bash/common/download_dataset.sh'
            }
        }
    }

    post {

        success {
            echo 'DATASET DOWNLOAD SUCCESSFUL'
        }

        failure {
            echo 'DATASET DOWNLOAD FAILED'
        }

        always {
            echo 'PIPELINE COMPLETED'
        }
    }
}