
pipeline {

    agent any

    parameters {

        choice(
            name: 'SOURCE_TYPE',
            choices: [
                'google_drive',
                'local'
            ],
            description: 'Select dataset source.'
        )

        string(
            name: 'SOURCE_PATH',
            defaultValue: '',
            description: 'Dataset location (Google Drive URL or local path)'
        )

        booleanParam(
            name: 'RUN_ASSESSMENT',
            defaultValue: true,
            description: 'Run database assessment after successful load.'
        )
    }

    stages {

        stage('Download Dataset') {
            steps {
                withEnv([
                    "SOURCE_TYPE=${params.SOURCE_TYPE}",
                    "SOURCE_PATH=${params.SOURCE_PATH}",
                    "DATABASE=mssql"
                ]) {
                    bat 'scripts\\batch\\common\\download_dataset.bat'
                }
            }
        }

        stage('Verify Download') {
            steps {
                    bat 'python scripts\\python\\common\\verify_download.py'
                }
            }
        }

        // stage('Assessment Report') {
        //     when {
        //         expression {
        //             return params.RUN_ASSESSMENT == true
        //         }
        //     }

        //     steps {
        //         bat 'scripts\\batch\\mssql\\migration\\run_migration_pipeline.bat'
        //     }
        // }
    
}

