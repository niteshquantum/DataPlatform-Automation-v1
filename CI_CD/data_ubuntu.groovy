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

                script {

                    runTrackedStage('Install Python Requirements') {

                        sh './scripts/bash/postgresql/setup/install_python_requirements.sh'
                    }
                }
            }
        }

                stage('Download Dataset') {

            steps {

                script {

                    runTrackedStage('Download Dataset') {

                        sh './scripts/bash/common/download_dataset.sh'
                    }
                }
            }
        }
    }
}