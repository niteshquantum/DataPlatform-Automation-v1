

def execute(Map context) {
    def runTrackedStage = context.runTrackedStage ?: { String stageName, Closure stageBody -> stageBody() }


        stage('Set Permissions') {


                sh '''
                    find scripts/bash -type f -name "*.sh" -exec chmod +x {} \\;
                '''
        }


        


        stage('Validate Python Runtime') {



                    runTrackedStage('Validate Python Runtime') {

                        sh './scripts/bash/common/validate_python_runtime.sh'
                    }
        }


        stage('Install Python Requirements') {



                    runTrackedStage('Install Python Requirements') {

                        sh './scripts/bash/mssql/setup/install_python_requirements.sh'
                    }
        }


        stage('Validate Python Requirements') {



                    runTrackedStage('Validate Python Requirements') {

                        sh './scripts/bash/mssql/setup/validate_python_requirements.sh'
                    }
        }


        stage('Validate Java Runtime') {



                    runTrackedStage('Validate Java Runtime') {

                        sh './scripts/bash/common/validate_java_runtime.sh'
                    }
        }


        stage('Install Tools') {



                    runTrackedStage('Install Tools') {

                        sh './scripts/bash/mssql/setup/install_tools.sh'
                    }
        }


        stage('Check MSSQL Instance') {



                    runTrackedStage('Check MSSQL Instance') {

                        def output = sh(
                            script: 'bash scripts/bash/mssql/setup/check_instance.sh || true',
                            returnStdout: true
                        ).trim()

                        def lines = output.split('\n')
                        def state = 'UNKNOWN'

                        for (int i = 0; i < lines.size(); i++) {

                            def line = lines[i]

                            if (line.startsWith('INSTANCE_STATE=')) {

                                state = line.split('=', 2)[1].trim()

                                break
                            }
                        }

                        env.MSSQL_INITIAL_INSTANCE_STATE = state

                        echo "Instance State: ${state}"

                        if (state == 'PORT_OCCUPIED_BY_NON_MSSQL') {

                            error "Port conflict: configured MSSQL port is occupied by a non-MSSQL process. Aborting setup."
                        }

                        if (state == 'UNKNOWN') {

                            error "Unknown MSSQL instance state detected. Aborting setup."
                        }
                    }
        }


        if ({ -> return env.MSSQL_INITIAL_INSTANCE_STATE == 'NO_INSTANCE' }()) {
            stage('Install MSSQL') {runTrackedStage('Install MSSQL') {

                        sh './scripts/bash/mssql/setup/install_mssql.sh'
                    }
                }
        }


        if ({ -> return env.MSSQL_INITIAL_INSTANCE_STATE == 'NO_INSTANCE' }()) {
            stage('Deploy MSSQL') {runTrackedStage('Deploy MSSQL') {

                        sh './scripts/bash/mssql/setup/deploy_mssql.sh'
                    }
                }
        }


        if ({ -> def state = env.MSSQL_INITIAL_INSTANCE_STATE
                    return state == 'INSTANCE_INSTALLED_BUT_STOPPED' || state == 'NO_INSTANCE' }()) {
            stage('Start MSSQL') {runTrackedStage('Start MSSQL') {

                        sh './scripts/bash/mssql/setup/start_mssql.sh'
                    }
                }
                    }


        if ({ -> return env.MSSQL_INITIAL_INSTANCE_STATE != 'INSTANCE_RUNNING_AND_USABLE' }()) {
            stage('Configure Global MSSQL') {runTrackedStage('Configure Global MSSQL') {

                        sh 'bash ./scripts/bash/mssql/setup/configure_global_mssql.sh'
                    }
                }
        }


//         stage('Configure Database RBAC') {
// runTrackedStage('Configure Database RBAC') { sh './scripts/bash/mssql/setup/create_database.sh'; sh './scripts/bash/mssql/rbac/configure_database_rbac.sh'; sh './scripts/bash/mssql/setup/run_liquibase.sh' }
//         }

                stage('Validate Environment') {
                    runTrackedStage('Validate Environment') {
                        sh './scripts/bash/mssql/setup/validate_environment.sh'
                    }
                }

        }   // execute() end

        return this