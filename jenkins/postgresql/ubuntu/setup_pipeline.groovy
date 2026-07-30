def runTrackedStage(String stageName, Closure stageBody) {

    sh """
        python3 scripts/logging/logger.py stage-start \
        --database postgresql \
        --action setup \
        --build-number "${env.BUILD_NUMBER}" \
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        sh """
            python3 scripts/logging/logger.py stage-end \
            --database postgresql \
            --action setup \
            --build-number "${env.BUILD_NUMBER}" \
            --stage-name "${stageName}" \
            --status SUCCESS
        """

    } catch (Exception error) {

        sh """
            python3 scripts/logging/logger.py stage-end \
            --database postgresql \
            --action setup \
            --build-number "${env.BUILD_NUMBER}" \
            --stage-name "${stageName}" \
            --status FAILURE
        """

        sh """
            python3 scripts/logging/logger.py set-error \
            --database postgresql \
            --action setup \
            --build-number "${env.BUILD_NUMBER}" \
            --failed-stage "${stageName}" \
            --message "Stage execution failed"
        """

        throw error
    }
}


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


        stage('Initialize Logging') {

            steps {

                script {

                    sh """
                        python3 scripts/logging/logger.py init \
                        --database postgresql \
                        --action setup \
                        --os ubuntu \
                        --build-number "${env.BUILD_NUMBER}" \
                        --job-name "${env.JOB_NAME}" \
                        --build-url "${env.BUILD_URL}"
                    """

                    env.POSTGRESQL_SETUP_LOGGING_INITIALIZED = 'true'
                }
            }
        }


        stage('Validate Python Runtime') {

            steps {

                script {

                    runTrackedStage('Validate Python Runtime') {

                        sh './scripts/bash/common/validate_python_runtime.sh'
                    }
                }
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


        stage('Validate Python Requirements') {

            steps {

                script {

                    runTrackedStage('Validate Python Requirements') {

                        sh './scripts/bash/postgresql/setup/validate_python_requirements.sh'
                    }
                }
            }
        }


        stage('Validate Java Runtime') {

            steps {

                script {

                    runTrackedStage('Validate Java Runtime') {

                        sh './scripts/bash/common/validate_java_runtime.sh'
                    }
                }
            }
        }


        stage('Install Tools') {

            steps {

                script {

                    runTrackedStage('Install Tools') {

                        sh './scripts/bash/postgresql/setup/install_tools.sh'
                    }
                }
            }
        }


        stage('Check PostgreSQL Instance') {

            steps {

                script {

                    runTrackedStage('Check PostgreSQL Instance') {

                        def output = sh(
                            script: 'bash scripts/bash/postgresql/setup/check_instance.sh || true',
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

                        env.POSTGRESQL_INITIAL_INSTANCE_STATE = state

                        echo "Instance State: ${state}"

                        if (state == 'PORT_OCCUPIED_BY_NON_POSTGRESQL') {

                            error "Port conflict: configured PostgreSQL port is occupied by a non-PostgreSQL process. Aborting setup."
                        }

                        if (state == 'UNKNOWN') {

                            error "Unknown PostgreSQL instance state detected. Aborting setup."
                        }
                    }
                }
            }
        }


        stage('Install PostgreSQL') {

            when {
                expression {
                    return env.POSTGRESQL_INITIAL_INSTANCE_STATE == 'NO_INSTANCE'
                }
            }

            steps {

                script {

                    runTrackedStage('Install PostgreSQL') {

                        sh './scripts/bash/postgresql/setup/install_postgresql.sh'
                    }
                }
            }
        }


        stage('Deploy PostgreSQL') {

            when {
                expression {
                    return env.POSTGRESQL_INITIAL_INSTANCE_STATE == 'NO_INSTANCE'
                }
            }

            steps {

                script {

                    runTrackedStage('Deploy PostgreSQL') {

                        sh './scripts/bash/postgresql/setup/deploy_postgresql.sh'
                    }
                }
            }
        }


        stage('Start PostgreSQL') {

            when {
                expression {
                    def state = env.POSTGRESQL_INITIAL_INSTANCE_STATE
                    return state == 'INSTANCE_INSTALLED_BUT_STOPPED' || state == 'NO_INSTANCE'
                }
            }

            steps {

                script {

                    runTrackedStage('Start PostgreSQL') {

                        sh './scripts/bash/postgresql/setup/start_postgresql.sh'
                    }
                }
            }
        }


        stage('Configure PostgreSQL User') {

            steps {

                script {

                    runTrackedStage('Configure PostgreSQL User') {

                        sh './scripts/bash/postgresql/setup/configure_postgresql.sh'
                    }
                }
            }
        }


        stage('Configure Global PSQL') {

            when {
                expression {
                    return env.POSTGRESQL_INITIAL_INSTANCE_STATE != 'INSTANCE_RUNNING_AND_USABLE'
                }
            }

            steps {

                script {

                    runTrackedStage('Configure Global PSQL') {

                        sh 'bash ./scripts/bash/postgresql/setup/configure_global_psql.sh'
                    }
                }
            }
        }


        stage('Configure Database RBAC') {
            steps { script { runTrackedStage('Configure Database RBAC') { sh './scripts/bash/postgresql/setup/create_database.sh'; sh './scripts/bash/postgresql/rbac/configure_database_rbac.sh'; sh './scripts/bash/postgresql/setup/run_liquibase.sh' } } }
        }

        stage('Validate Environment') {

            steps {

                script {

                    runTrackedStage('Validate Environment') {

                        sh './scripts/bash/postgresql/setup/validate_environment.sh'
                    }
                }
            }
        }
    }


    post {

        success {

            echo 'UBUNTU POSTGRESQL SETUP SUCCESSFUL'
        }


        failure {

            echo 'UBUNTU POSTGRESQL SETUP FAILED'
        }


        always {

            echo 'FINALIZING UBUNTU POSTGRESQL SETUP LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult

                if (env.POSTGRESQL_SETUP_LOGGING_INITIALIZED == 'true') {

                    sh """
                        python3 scripts/logging/logger.py finalize \
                            --database postgresql \
                            --action setup \
                            --build-number "${env.BUILD_NUMBER}" \
                            --status "${finalStatus}"
                    """

                    sh """
                        python3 scripts/reporting/generate_report.py \
                            --database postgresql \
                            --action setup \
                            --build-number "${env.BUILD_NUMBER}"
                    """

                    sh """
                        python3 scripts/reporting/generate_history.py \
                            --database postgresql \
                            --action setup \
                            --build-number "${env.BUILD_NUMBER}"
                    """
                } else {

                    echo 'SKIPPING FINALIZE/REPORT: logging was not initialized'
                }
            }


            archiveArtifacts(
                artifacts: "logs/postgresql/setup/build_${env.BUILD_NUMBER}/**, reports/postgresql/setup/build_${env.BUILD_NUMBER}/**, reports/history/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo 'UBUNTU POSTGRESQL SETUP PIPELINE COMPLETED'
        }
    }
}
