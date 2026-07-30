def runTrackedStage(String stageName, Closure stageBody) {

    sh """
        python3 scripts/logging/logger.py stage-start \
        --database postgresql \
        --action load \
        --build-number "${env.BUILD_NUMBER}" \
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        sh """
            python3 scripts/logging/logger.py stage-end \
            --database postgresql \
            --action load \
            --build-number "${env.BUILD_NUMBER}" \
            --stage-name "${stageName}" \
            --status SUCCESS
        """

    } catch (Exception error) {

        sh """
            python3 scripts/logging/logger.py stage-end \
                --database postgresql \
                --action load \
                --build-number "${env.BUILD_NUMBER}" \
                --stage-name "${stageName}" \
                --status FAILURE
        """

        sh """
            python3 scripts/logging/logger.py set-error \
                --database postgresql \
                --action load \
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
                        --action load \
                        --os ubuntu \
                        --build-number "${env.BUILD_NUMBER}" \
                        --job-name "${env.JOB_NAME}" \
                        --build-url "${env.BUILD_URL}"
                    """

                    env.POSTGRESQL_LOAD_LOGGING_INITIALIZED = 'true'
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


        stage('Validate Python Requirements') {

            steps {

                script {

                    runTrackedStage('Validate Python Requirements') {

                        sh './scripts/bash/postgresql/setup/validate_python_requirements.sh'
                    }
                }
            }
        }


        stage('Start PostgreSQL') {

            steps {

                script {

                    runTrackedStage('Start PostgreSQL') {

                        sh './scripts/bash/postgresql/setup/start_postgresql.sh'
                    }
                }
            }
        }


        stage('Validate PostgreSQL Instance') {

            steps {

                script {

                    runTrackedStage('Validate PostgreSQL Instance') {

                        sh './scripts/bash/postgresql/setup/validate_postgresql.sh'
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


        stage('Profile Source Data') {

            steps {

                script {

                    runTrackedStage('Profile Source Data') {

                        sh './scripts/bash/common/run_data_profiling.sh postgresql'
                    }
                }
            }
        }


        stage('Create Database') {

            steps {

                script {

                    runTrackedStage('Create Database') {

                        sh './scripts/bash/postgresql/setup/create_database.sh'
                    }
                }
            }
        }


        stage('Run CDC') {

            steps {

                script {

                    runTrackedStage('Run CDC') {

                        sh './scripts/bash/postgresql/load/run_cdc.sh'
                    }
                }
            }
        }


        stage('Load Data') {

            steps {

                script {

                    runTrackedStage('Load Data') {

                        sh './scripts/bash/postgresql/load/load_data.sh'
                    }
                }
            }
        }


        stage('Validate Loaded Data') {

            steps {

                script {

                    runTrackedStage('Validate Loaded Data') {

                        sh './scripts/bash/postgresql/load/validate_loaded_data.sh'
                    }
                }
            }
        }


        stage('Deploy Database Objects') {

            steps {

                script {

                    runTrackedStage('Deploy Database Objects') {

                        sh './scripts/bash/postgresql/objects/deploy_objects.sh'
                    }
                }
            }
        }


        stage('Validate Database Objects') {

            steps {

                script {

                    runTrackedStage('Validate Database Objects') {

                        sh './scripts/bash/postgresql/objects/validate_objects.sh'
                    }
                }
            }
        }


        stage('Database Assessment') {

            steps {

                script {

                    runTrackedStage('Database Assessment') {

                        sh './scripts/bash/postgresql/assessment/run_assessment.sh all'
                    }
                }
            }
        }


        stage('Assessment Report') {

            steps {

                script {

                    runTrackedStage('Assessment Report') {

                        sh './scripts/bash/common/generate_assessment_report.sh'
                    }
                }
            }
        }


        stage('Reconcile Source and Target Data') {

            steps {

                script {

                    runTrackedStage(
                        'Reconcile Source and Target Data'
                    ) {

                        sh './scripts/bash/common/run_reconciliation.sh postgresql'
                    }
                }
            }
        }


        stage('Discover Database Environment') {

            steps {

                script {

                    runTrackedStage(
                        'Discover Database Environment'
                    ) {

                        sh 'python3 scripts/discovery/discovery_engine.py --database postgresql'
                    }
                }
            }
        }


        stage('Analyze Database Growth') {

            steps {

                script {

                    runTrackedStage(
                        'Analyze Database Growth'
                    ) {

                        sh 'python3 scripts/discovery/growth_analyzer.py --database postgresql'
                    }
                }
            }
        }


        stage('Analyze Migration Requirements') {

            steps {

                script {

                    runTrackedStage(
                        'Analyze Migration Requirements'
                    ) {

                        sh 'python3 scripts/discovery/requirement_analyzer.py --database postgresql'
                    }
                }
            }
        }


        stage('Assess Migration') {

            steps {

                script {

                    runTrackedStage('Assess Migration') {

                        sh './scripts/bash/common/run_assessment.sh postgresql'
                    }
                }
            }
        }


        stage('Generate Migration Recommendations') {

            steps {

                script {

                    runTrackedStage(
                        'Generate Migration Recommendations'
                    ) {

                        sh './scripts/bash/common/run_recommendation.sh postgresql'
                    }
                }
            }
        }


        stage('Generate Governance Action Plan') {

            steps {

                script {

                    runTrackedStage(
                        'Generate Governance Action Plan'
                    ) {

                        sh './scripts/bash/common/run_action_plan.sh postgresql'
                    }
                }
            }
        }


        stage('Generate Technical Migration Report') {

            steps {

                script {

                    runTrackedStage(
                        'Generate Technical Migration Report'
                    ) {

                        sh './scripts/bash/common/generate_technical_report.sh postgresql'
                    }
                }
            }
        }


        stage('Generate Executive Migration Report') {

            steps {

                script {

                    runTrackedStage(
                        'Generate Executive Migration Report'
                    ) {

                        sh './scripts/bash/common/generate_executive_report.sh postgresql'
                    }
                }
            }
        }
    }


    post {

        success {

            echo 'UBUNTU POSTGRESQL LOAD SUCCESSFUL'
        }


        failure {

            echo 'UBUNTU POSTGRESQL LOAD FAILED'
        }


        always {

            echo 'FINALIZING UBUNTU POSTGRESQL LOAD LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult

                if (env.POSTGRESQL_LOAD_LOGGING_INITIALIZED == 'true') {

                    sh """
                        python3 scripts/logging/logger.py finalize \
                            --database postgresql \
                            --action load \
                            --build-number "${env.BUILD_NUMBER}" \
                            --status "${finalStatus}"
                    """

                    sh """
                        python3 scripts/reporting/generate_report.py \
                            --database postgresql \
                            --action load \
                            --build-number "${env.BUILD_NUMBER}"
                    """

                    sh """
                        python3 scripts/reporting/generate_history.py \
                            --database postgresql \
                            --action load \
                            --build-number "${env.BUILD_NUMBER}"
                    """
                } else {

                    echo 'SKIPPING FINALIZE/REPORT: logging was not initialized'
                }
            }


            archiveArtifacts(
                artifacts: "logs/postgresql/load/build_${env.BUILD_NUMBER}/**, reports/postgresql/load/build_${env.BUILD_NUMBER}/**, reports/history/**, reports/migration/postgresql/**, outputs/assessments/postgresql/**, outputs/assessments/assessment_report.json, metadata/profiling/postgresql/**, metadata/reconciliation/postgresql/**, metadata/discovery/postgresql/**, metadata/assessment/postgresql/**, metadata/recommendation/postgresql/**, metadata/governance/postgresql/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo 'UBUNTU POSTGRESQL LOAD PIPELINE COMPLETED'
        }
    }
}
