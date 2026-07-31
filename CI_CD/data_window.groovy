pipeline {

    agent any

    options {
        disableConcurrentBuilds()
    }

    stages {

        stage('Install Python Requirements') {

            steps {

                bat 'scripts\\batch\\postgresql\\setup\\install_python_requirements.bat'
            }
        }

        stage('Download Dataset') {

            steps {

                bat 'scripts\\batch\\common\\download_dataset.bat'
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