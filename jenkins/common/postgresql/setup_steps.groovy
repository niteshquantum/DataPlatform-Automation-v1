


def getInstanceState() {

    def output = bat(
        script: 'scripts\\batch\\postgresql\\setup\\check_instance.bat',
        returnStdout: true
    ).trim()

    def state = 'UNKNOWN'

    def lines = output.split('\n')

    for (int i = 0; i < lines.size(); i++) {

        def line = lines[i]

        if (line.startsWith('INSTANCE_STATE=')) {

            state = line.split('=', 2)[1]

            break
        }
    }

    return state
}

def execute(Map context) {
    def runTrackedStage = context.runTrackedStage ?: { String stageName, Closure stageBody -> stageBody() }


       


        stage('Check Administrator Privileges') {



                    runTrackedStage(
                        'Check Administrator Privileges'
                    ) {

                        def adminStatus = bat(
                            script: 'scripts\\batch\\common\\check_admin_privileges.bat',
                            returnStatus: true
                        )

                        if (adminStatus == 0) {

                            writeFile(
                                file: 'admin_status.txt',
                                text: 'true'
                            )

                            echo 'Administrator privileges available.'
                            echo 'PostgreSQL Service and Global PSQL configuration will be enabled.'

                        } else {

                            writeFile(
                                file: 'admin_status.txt',
                                text: 'false'
                            )

                            echo 'Administrator privileges not available.'
                            echo 'PostgreSQL Service and Global PSQL configuration will be skipped.'
                            echo 'PostgreSQL will run using project-local mode.'
                        }

                        def adminResult = readFile(
                            'admin_status.txt'
                        ).trim()

                        echo "ADMIN STATUS = ${adminResult}"

                        bat """
                            python scripts\\logging\\logger.py set-environment ^
                            --database postgresql ^
                            --action setup ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --administrator-privileges "${adminResult}"
                        """
                    }
        }


        stage('Validate Python Runtime') {



                    runTrackedStage(
                        'Validate Python Runtime'
                    ) {

                        bat 'scripts\\batch\\common\\validate_python_runtime.bat'
                    }
        }


        stage('Install Python Requirements') {



                    runTrackedStage(
                        'Install Python Requirements'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\install_python_requirements.bat'
                    }
        }


        stage('Validate Python Requirements') {



                    runTrackedStage(
                        'Validate Python Requirements'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\validate_python_requirements.bat'
                    }
        }


        stage('Validate Java Runtime') {



                    runTrackedStage(
                        'Validate Java Runtime'
                    ) {

                        bat 'scripts\\batch\\common\\validate_java_runtime.bat'
                    }
        }


        stage('Install Tools') {



                    runTrackedStage(
                        'Install Tools'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\install_tools.bat'
                    }
        }


        stage('Check PostgreSQL Instance') {



                    runTrackedStage(
                        'Check PostgreSQL Instance'
                    ) {

                        def instanceState = getInstanceState()

                        env.POSTGRESQL_INITIAL_INSTANCE_STATE = instanceState

                        echo "Instance State: ${instanceState}"

                        if (instanceState == 'PORT_OCCUPIED_BY_NON_POSTGRESQL') {

                            error "Port conflict: configured PostgreSQL port is occupied by a non-PostgreSQL process. Aborting setup."
                        }

                        if (instanceState == 'POSTGRESQL_AUTHENTICATION_FAILED') {

                            error "PostgreSQL is reachable on the configured port, but the configured credentials were rejected. Aborting setup."
                        }

                        if (instanceState == 'UNKNOWN') {

                            error "Unknown PostgreSQL instance state detected. Aborting setup."
                        }
                    }
        }


    def startInstanceState = getInstanceState()

    if (startInstanceState == 'NO_INSTANCE') {
        stage('Deploy PostgreSQL') {

            runTrackedStage(
                'Deploy PostgreSQL'
            ) {
                bat 'scripts\\batch\\postgresql\\setup\\deploy_postgresql.bat'
            }
        }
    }

    if (startInstanceState == 'INSTANCE_INSTALLED_BUT_STOPPED' ||
        startInstanceState == 'NO_INSTANCE') {

        stage('Start PostgreSQL') {

            runTrackedStage(
                'Start PostgreSQL'
            ) {

                echo 'Starting PostgreSQL...'

                bat 'scripts\\batch\\postgresql\\setup\\start_postgresql.bat'
            }
        }
    }

        stage('Validate PostgreSQL Instance') {



                    runTrackedStage(
                        'Validate PostgreSQL Instance'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\validate_postgresql.bat'
                    }
        }


        if (readFile('admin_status.txt').trim() == 'true') {
           stage('Configure PostgreSQL Service') {

                runTrackedStage(
                    'Configure PostgreSQL Service'
                ) {

                    bat 'scripts\\batch\\postgresql\\setup\\configure_postgresql_service.bat'
                }
            }
        }
        
        if (readFile('admin_status.txt').trim() == 'true') {
           stage('Configure Global PSQL') {

            runTrackedStage(
                'Configure Global PSQL'
            ) {

                echo 'Administrator privileges available.'
                echo 'Configuring Global PSQL command...'

                bat 'scripts\\batch\\postgresql\\setup\\configure_global_psql.bat'
            }
        }
        }

        // stage('Configure Database RBAC') {
        // runTrackedStage('Configure Database RBAC') { bat 'scripts\\batch\\postgresql\\setup\\create_database.bat'; bat 'scripts\\batch\\postgresql\\rbac\\configure_database_rbac.bat'; bat 'scripts\\batch\\postgresql\\setup\\run_liquibase.bat' }
        // }

        stage('Validate Environment') {

    runTrackedStage(
        'Validate Environment'
    ) {

        bat 'scripts\\batch\\postgresql\\setup\\validate_environment.bat'
    }
}

}

return this
