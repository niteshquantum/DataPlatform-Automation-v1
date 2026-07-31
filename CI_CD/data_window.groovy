pipeline {

    agent any

    options {
        disableConcurrentBuilds()
    }

    stages {
                    stage('Install Python Requirements') {

            steps {

                script {

                    runTrackedStage(
                        'Install Python Requirements'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\install_python_requirements.bat'
                    }
                }
            }
        }

                stage('Download Dataset') {

            steps {

                script {

                    runTrackedStage('Download Dataset') {

                        bat 'scripts\\batch\\common\\download_dataset.bat'
                    }
                }
            }
        }

    }
}