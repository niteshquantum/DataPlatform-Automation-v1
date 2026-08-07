def runTrackedStage(String stageName, Closure stageBody) {

    sh """
        python3 scripts/logging/logger.py stage-start \
        --database mysql \
        --action load \
        --build-number "${env.BUILD_NUMBER}" \
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        sh """
            python3 scripts/logging/logger.py stage-end \
            --database mysql \
            --action load \
            --build-number "${env.BUILD_NUMBER}" \
            --stage-name "${stageName}" \
            --status SUCCESS
        """

    } catch (Exception error) {

        sh """
            python3 scripts/logging/logger.py stage-end \
            --database mysql \
            --action load \
            --build-number "${env.BUILD_NUMBER}" \
            --stage-name "${stageName}" \
            --status FAILURE
        """

        sh """
            python3 scripts/logging/logger.py set-error \
            --database mysql \
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

        stage('Initialize Logging') {

            steps {

                sh """
                    python3 scripts/logging/logger.py init \
                    --database mysql \
                    --action load \
                    --os ubuntu \
                    --build-number "${env.BUILD_NUMBER}" \
                    --job-name "${env.JOB_NAME}" \
                    --build-url "${env.BUILD_URL}"
                """
            }
        }


        stage('Set Permissions') {

            steps {

                script {

                    runTrackedStage('Set Permissions') {

                        sh '''
                            find scripts/bash -type f -name "*.sh" -exec chmod +x {} \\;
                        '''
                    }
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

                        sh './scripts/bash/mysql/setup/validate_python_requirements.sh'
                    }
                }
            }
        }


        stage('Start MySQL') {

            steps {

                script {

                    runTrackedStage('Start MySQL') {

                        sh './scripts/bash/mysql/setup/start_mysql.sh'
                    }
                }
            }
        }


        stage('Validate MySQL Instance') {

            steps {

                script {

                    runTrackedStage('Validate MySQL Instance') {

                        sh './scripts/bash/mysql/setup/validate_mysql_instance.sh'
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

                        sh './scripts/bash/common/run_data_profiling.sh mysql'
                    }
                }
            }
        }
        stage('Schema Detection') {

            runTrackedStage(
                'Schema Detection'
            ) {

               sh 'python3 scripts/schema_detector.py mysql'
            }
        }

        stage('Datatype Detection') {

            runTrackedStage(
                'Datatype Detection'
            ) {

                sh 'python3 scripts/datatype_registry_generator.py mysql'
            }
        }

        stage('Schema Editor') {

            runTrackedStage(
                'Schema Editor'
            ) {

                sh 'python3 scripts/schema_editor/app.py mysql'
            }
        }

        stage('Create Database') {

            steps {

                script {

                    runTrackedStage('Create Database') {

                        sh './scripts/bash/mysql/setup/create_database.sh'
                    }
                }
            }
        }


        stage('Validate MySQL') {

            steps {

                script {

                    runTrackedStage('Validate MySQL') {

                        sh './scripts/bash/mysql/setup/validate_mysql.sh'
                    }
                }
            }
        }


        stage('Load Data') {

            steps {

                script {

                    runTrackedStage('Load Data') {

                        sh './scripts/bash/mysql/load/load_data.sh'
                    }
                }
            }
        }


        stage('Validate Loaded Data') {

            steps {

                script {

                    runTrackedStage('Validate Loaded Data') {

                        sh './scripts/bash/mysql/load/validate_loaded_data.sh'
                    }
                }
            }
        }


        stage('Deploy Database Objects') {

            steps {

                script {

                    runTrackedStage('Deploy Database Objects') {

                        sh './scripts/bash/mysql/objects/deploy_objects.sh'
                    }
                }
            }
        }


        stage('Validate Database Objects') {

            steps {

                script {

                    runTrackedStage('Validate Database Objects') {

                        sh './scripts/bash/mysql/objects/validate_objects.sh'
                    }
                }
            }
        }


        stage('Database Assessment') {

            steps {

                script {

                    runTrackedStage('Database Assessment') {

                        sh './scripts/bash/mysql/assessment/run_assessment.sh all'
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

                        sh './scripts/bash/common/run_reconciliation.sh mysql'
                    }

                    runTrackedStage(
                        'Discover Database Environment'
                    ) {

                        sh 'python3 scripts/discovery/discovery_engine.py --database mysql'
                    }

                    runTrackedStage(
                        'Analyze Database Growth'
                    ) {

                        sh 'python3 scripts/discovery/growth_analyzer.py --database mysql'
                    }

                    runTrackedStage(
                        'Analyze Migration Requirements'
                    ) {

                        sh 'python3 scripts/discovery/requirement_analyzer.py --database mysql'
                    }

                    runTrackedStage('Assess Migration') {

                        sh './scripts/bash/common/run_assessment.sh mysql'
                    }

                    runTrackedStage(
                        'Generate Migration Recommendations'
                    ) {

                        sh './scripts/bash/common/run_recommendation.sh mysql'
                    }

                    runTrackedStage(
                        'Generate Governance Action Plan'
                    ) {

                        sh './scripts/bash/common/run_action_plan.sh mysql'
                    }

                    runTrackedStage(
                        'Generate Technical Migration Report'
                    ) {

                        sh './scripts/bash/common/generate_technical_report.sh mysql'
                    }

                    runTrackedStage(
                        'Generate Executive Migration Report'
                    ) {

                        sh './scripts/bash/common/generate_executive_report.sh mysql'
                    }
                }
            }
        }
    }


    post {

        success {

            echo 'UBUNTU MYSQL LOAD SUCCESSFUL'
        }


        failure {

            echo 'UBUNTU MYSQL LOAD FAILED'
        }


        always {

            echo 'FINALIZING UBUNTU MYSQL LOAD LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult

                sh """
                    python3 scripts/logging/logger.py finalize \
                        --database mysql \
                        --action load \
                        --build-number "${env.BUILD_NUMBER}" \
                        --status "${finalStatus}"
                """

                sh """
                    python3 scripts/reporting/generate_report.py \
                        --database mysql \
                        --action load \
                        --build-number "${env.BUILD_NUMBER}"
                """

                sh """
                    python3 scripts/reporting/generate_history.py \
                        --database mysql \
                        --action load \
                        --build-number "${env.BUILD_NUMBER}"
                """
            }


            archiveArtifacts(
                artifacts: "logs/mysql/load/build_${env.BUILD_NUMBER}/**, reports/mysql/load/build_${env.BUILD_NUMBER}/**, reports/history/**, reports/migration/mysql/**, outputs/assessments/mysql/**, outputs/assessments/assessment_report.json, metadata/profiling/mysql/**, metadata/reconciliation/mysql/**, metadata/discovery/mysql/**, metadata/assessment/mysql/**, metadata/recommendation/mysql/**, metadata/governance/mysql/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo 'UBUNTU MYSQL LOAD PIPELINE COMPLETED'
        }
    }
}
