def runTrackedStage(String stageName, Closure stageBody) {

    sh """
        python3 scripts/logging/logger.py stage-start \
        --database mssql \
        --action load \
        --build-number "${env.BUILD_NUMBER}" \
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        sh """
            python3 scripts/logging/logger.py stage-end \
            --database mssql \
            --action load \
            --build-number "${env.BUILD_NUMBER}" \
            --stage-name "${stageName}" \
            --status SUCCESS
        """

    } catch (Exception error) {

        sh """
            python3 scripts/logging/logger.py stage-end \
                --database mssql \
                --action load \
                --build-number "${env.BUILD_NUMBER}" \
                --stage-name "${stageName}" \
                --status FAILURE
        """

        sh """
            python3 scripts/logging/logger.py set-error \
                --database mssql \
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
                        --database mssql \
                        --action load \
                        --os ubuntu \
                        --build-number "${env.BUILD_NUMBER}" \
                        --job-name "${env.JOB_NAME}" \
                        --build-url "${env.BUILD_URL}"
                    """

                    env.MSSQL_LOAD_LOGGING_INITIALIZED = 'true'
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

                        sh './scripts/bash/mssql/setup/install_python_requirements.sh'
                    }
                }
            }
        }


        stage('Validate Python Requirements') {

            steps {

                script {

                    runTrackedStage('Validate Python Requirements') {

                        sh './scripts/bash/mssql/setup/validate_python_requirements.sh'
                    }
                }
            }
        }


        stage('Validate Tools') {

            steps {

                script {

                    runTrackedStage('Validate Tools') {

                        sh './scripts/bash/mssql/validate_tools.sh'
                    }
                }
            }
        }


        stage('Start MSSQL') {

            steps {

                script {

                    runTrackedStage('Start MSSQL') {

                        sh './scripts/bash/mssql/setup/start_mssql.sh'
                    }
                }
            }
        }


        stage('Validate MSSQL Instance') {

            steps {

                script {

                    runTrackedStage('Validate MSSQL Instance') {

                        sh './scripts/bash/mssql/setup/validate_mssql_instance.sh'
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

                        sh './scripts/bash/common/run_data_profiling.sh mssql'
                    }
                }
            }
        }

        stage('Schema Detection') {

            runTrackedStage(
                'Schema Detection'
            ) {

                sh 'python3 scripts/schema_detector.py mssql'
            }
        }

        stage('Datatype Detection') {

            runTrackedStage(
                'Datatype Detection'
            ) {

                sh 'python3 scripts/datatype_registry_generator.py mssql'
            }
        }

        stage('Schema Editor') {

            runTrackedStage(
                'Schema Editor'
            ) {

                sh 'python3 scripts/schema_editor/app.py mssql'
            }
        }
        stage('Create Database') {

            steps {

                script {

                    runTrackedStage('Create Database') {

                        sh './scripts/bash/mssql/setup/create_database.sh'
                    }
                }
            }
        }


        stage('Validate MSSQL') {

            steps {

                script {

                    runTrackedStage('Validate MSSQL') {

                        sh './scripts/bash/mssql/setup/validate_mssql.sh'
                    }
                }
            }
        }


        stage('Load Data') {

            steps {

                script {

                    runTrackedStage('Load Data') {

                        sh './scripts/bash/mssql/load/load_data.sh'
                    }
                }
            }
        }


        stage('Validate Loaded Data') {

            steps {

                script {

                    runTrackedStage('Validate Loaded Data') {

                        sh './scripts/bash/mssql/load/validate_loaded_data.sh'
                    }
                }
            }
        }


        stage('Deploy Database Objects') {

            steps {

                script {

                    runTrackedStage('Deploy Database Objects') {

                        sh './scripts/bash/mssql/objects/deploy_objects.sh'
                    }
                }
            }
        }


        stage('Validate Database Objects') {

            steps {

                script {

                    runTrackedStage('Validate Database Objects') {

                        sh './scripts/bash/mssql/objects/validate_objects.sh'
                    }
                }
            }
        }


        stage('Database Assessment') {

            steps {

                script {

                    runTrackedStage('Database Assessment') {

                        sh './scripts/bash/mssql/assessment/run_assessment.sh all'
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

                    runTrackedStage(
                        'Reconcile Source and Target Data'
                    ) {

                        sh './scripts/bash/common/run_reconciliation.sh mssql'
                    }

                    runTrackedStage(
                        'Discover Database Environment'
                    ) {

                        sh 'python3 scripts/discovery/discovery_engine.py --database mssql'
                    }

                    runTrackedStage(
                        'Analyze Database Growth'
                    ) {

                        sh 'python3 scripts/discovery/growth_analyzer.py --database mssql'
                    }

                    runTrackedStage(
                        'Analyze Migration Requirements'
                    ) {

                        sh 'python3 scripts/discovery/requirement_analyzer.py --database mssql'
                    }

                    runTrackedStage('Assess Migration') {

                        sh './scripts/bash/common/run_assessment.sh mssql'
                    }

                    runTrackedStage(
                        'Generate Migration Recommendations'
                    ) {

                        sh './scripts/bash/common/run_recommendation.sh mssql'
                    }

                    runTrackedStage(
                        'Generate Governance Action Plan'
                    ) {

                        sh './scripts/bash/common/run_action_plan.sh mssql'
                    }

                    runTrackedStage(
                        'Generate Technical Migration Report'
                    ) {

                        sh './scripts/bash/common/generate_technical_report.sh mssql'
                    }

                    runTrackedStage(
                        'Generate Executive Migration Report'
                    ) {

                        sh './scripts/bash/common/generate_executive_report.sh mssql'
                    }
                }
            }
        }
    }


    post {

        success {

            echo 'UBUNTU MSSQL LOAD SUCCESSFUL'
        }


        failure {

            echo 'UBUNTU MSSQL LOAD FAILED'
        }


        always {

            echo 'FINALIZING UBUNTU MSSQL LOAD LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult

                if (env.MSSQL_LOAD_LOGGING_INITIALIZED == 'true') {

                    sh """
                        python3 scripts/logging/logger.py finalize \
                            --database mssql \
                            --action load \
                            --build-number "${env.BUILD_NUMBER}" \
                            --status "${finalStatus}"
                    """

                    sh """
                        python3 scripts/reporting/generate_report.py \
                            --database mssql \
                            --action load \
                            --build-number "${env.BUILD_NUMBER}"
                    """

                    sh """
                        python3 scripts/reporting/generate_history.py \
                            --database mssql \
                            --action load \
                            --build-number "${env.BUILD_NUMBER}"
                    """
                } else {

                    echo 'SKIPPING FINALIZE/REPORT: logging was not initialized'
                }
            }

            archiveArtifacts(
                artifacts: "logs/mssql/load/build_${env.BUILD_NUMBER}/**, reports/mssql/load/build_${env.BUILD_NUMBER}/**, reports/history/**, reports/migration/mssql/**, outputs/assessments/mssql/**, outputs/assessments/assessment_report.json, metadata/profiling/mssql/**, metadata/reconciliation/mssql/**, metadata/discovery/mssql/**, metadata/assessment/mssql/**, metadata/recommendation/mssql/**, metadata/governance/mssql/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo 'UBUNTU MSSQL LOAD PIPELINE COMPLETED'
        }
    }
}
