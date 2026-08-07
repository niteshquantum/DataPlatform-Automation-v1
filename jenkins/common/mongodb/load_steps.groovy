def execute(Map context) {
    def runTrackedStage = context.runTrackedStage ?: { String stageName, Closure stageBody -> stageBody() }

    stage('Validate Python Runtime') {

        runTrackedStage(
            'Validate Python Runtime'
        ) {
            bat 'scripts\\batch\\common\\validate_python_runtime.bat'
        }
    }

    stage('Validate MongoDB Requirements') {

        runTrackedStage(
            'Validate MongoDB Requirements'
        ) {
            bat 'scripts\\batch\\mongodb\\setup\\validate_python_requirements.bat'
        }
    }

    stage('Install Tools') {

        runTrackedStage(
            'Install Tools'
        ) {
            bat 'scripts\\batch\\mongodb\\setup\\install_tools.bat'
        }
    }

    stage('Validate Tools') {

        runTrackedStage(
            'Validate Tools'
        ) {
            bat 'scripts\\batch\\mongodb\\setup\\validate_tools.bat'
        }
    }

    stage('Check Instance State') {

        runTrackedStage(
            'Check Instance State'
        ) {

            def output = bat(
                script: 'scripts\\batch\\mongodb\\setup\\check_instance.bat',
                returnStdout: true
            ).trim()

            def instanceState = 'UNKNOWN'
            def instanceError = ''

            if (output) {

                def lines = output.split('\\r?\\n')

                for (int i = 0; i < lines.size(); i++) {

                    def line = lines[i].trim()

                    if (line.startsWith('INSTANCE_STATE=')) {
                        instanceState = line.split('=', 2)[1].trim()
                    }

                    if (line.startsWith('ERROR=')) {
                        instanceError = line.split('=', 2)[1].trim()
                    }
                }
            }

            def allowedStates = [
                'INSTANCE_RUNNING_AND_USABLE',
                'INSTANCE_INSTALLED_BUT_STOPPED',
                'NO_INSTANCE',
                'PORT_OCCUPIED_BY_NON_MONGODB'
            ]

            if (instanceState == 'UNKNOWN' || !allowedStates.contains(instanceState)) {
                error "check_instance.bat produced no valid instance state output. ${output ? 'Partial output: ' + output : 'Empty output'}"
            }

            echo "Instance state: ${instanceState}"

            if (instanceError) {
                echo "Instance error: ${instanceError}"
            }

            if (instanceState == 'INSTANCE_INSTALLED_BUT_STOPPED') {
                echo 'Managed instance stopped. Starting...'
                bat 'scripts\\batch\\mongodb\\setup\\start_mongodb.bat'
            } else if (instanceState == 'NO_INSTANCE') {
                error "No managed MongoDB instance found. Run SETUP first to deploy and configure MongoDB. ${instanceError}"
            } else if (instanceState == 'PORT_OCCUPIED_BY_NON_MONGODB') {
                error "Foreign process detected on MongoDB port. Aborting LOAD to avoid reusing an unmanaged listener. ${instanceError}"
            }
        }
    }

    stage('Validate MongoDB Instance') {

        runTrackedStage(
            'Validate MongoDB Instance'
        ) {
            bat 'scripts\\batch\\mongodb\\setup\\validate_mongodb.bat'
        }
    }

    stage('Download Dataset') {

        runTrackedStage(
            'Download Dataset'
        ) {
            bat 'scripts\\batch\\common\\download_dataset.bat'
        }
    }

    stage('Profile Source Data') {

        runTrackedStage(
            'Profile Source Data'
        ) {
            bat 'python scripts\\profiling\\data_profiler.py --database mongodb'
        }
    }
        stage('Schema Detection') {

        runTrackedStage(
            'Schema Detection'
        ) {
            bat 'python scripts\\schema_detector.py mongodb'
        }
    }

    stage('Datatype Detection') {

        runTrackedStage(
            'Datatype Detection'
        ) {
            bat 'python scripts\\datatype_registry_generator.py mongodb'
        }
    }

    stage('Schema Editor') {

        runTrackedStage(
            'Schema Editor'
        ) {
            bat 'python scripts\\schema_editor\\app.py mongodb'
        }
    }
    if (env.SKIP_DATA_LOAD != 'true') {

        stage('Load Data') {

            runTrackedStage(
                'Load Data'
            ) {
                bat 'scripts\\batch\\mongodb\\load\\load_data.bat'
            }
        }
    }

    if (env.SKIP_DATA_LOAD != 'true') {

        stage('Validate Loaded Data') {

            runTrackedStage(
                'Validate Loaded Data'
            ) {
                bat 'scripts\\batch\\mongodb\\load\\validate_loaded_data.bat'
            }
        }
    }

    if (params.RUN_ASSESSMENT == 'true') {

        stage('Database Assessment') {

            runTrackedStage(
                'Database Assessment'
            ) {
                bat 'scripts\\batch\\mongodb\\assessment\\run_assessment.bat all'
            }
        }
    }

    if (params.RUN_ASSESSMENT == 'true') {

        stage('Assessment Report') {

            runTrackedStage(
                'Assessment Report'
            ) {
                bat 'scripts\\batch\\common\\generate_assessment_report.bat'
            }
        }
    }
}

return this
