def runTrackedStage(String stageName, Closure stageBody) {

    bat """
        python scripts\\logging\\logger.py stage-start ^
        --database mongodb ^
        --action load ^
        --build-number "${env.BUILD_NUMBER}" ^
        --stage-name "${stageName}"
    """

    try {

        stageBody()

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mongodb ^
            --action load ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status SUCCESS
        """

    } catch (Exception error) {

        bat """
            python scripts\\logging\\logger.py stage-end ^
            --database mongodb ^
            --action load ^
            --build-number "${env.BUILD_NUMBER}" ^
            --stage-name "${stageName}" ^
            --status FAILURE
        """

        bat """
            python scripts\\logging\\logger.py set-error ^
            --database mongodb ^
            --action load ^
            --build-number "${env.BUILD_NUMBER}" ^
            --failed-stage "${stageName}" ^
            --message "Stage execution failed"
        """

        throw error
    }
}


pipeline {

    agent any

    parameters {

        booleanParam(
            name: 'RUN_ASSESSMENT',
            defaultValue: true,
            description: 'Run database assessment after successful load.'
        )
    }


    options {
        disableConcurrentBuilds()
    }


    stages {

        stage('Initialize Logging') {

            steps {

                bat """
                    python scripts\\logging\\logger.py init ^
                    --database mongodb ^
                    --action load ^
                    --os windows ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --job-name "${env.JOB_NAME}" ^
                    --build-url "${env.BUILD_URL}"
                """
            }
        }


        stage('Validate Python Runtime') {

            steps {

                bat 'scripts\\batch\\common\\validate_python_runtime.bat'
            }
        }


        stage('Validate Python Requirements') {

            steps {

                bat 'scripts\\batch\\mongodb\\setup\\validate_python_requirements.bat'
            }
        }


        stage('Check Instance State') {

            steps {

                script {

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
                            def lines = output.split('\r?\n')
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

                        if (!output || instanceState == 'UNKNOWN') {
                            throw new Exception("check_instance.bat produced no valid instance state output. ${output ? 'Partial output: ' + output : 'Empty output'}")
                        }

                        echo "Instance state: ${instanceState}"
                        if (instanceError) {
                            echo "Instance error: ${instanceError}"
                        }

                        if (instanceState == 'INSTANCE_RUNNING_AND_USABLE') {
                            echo 'Managed instance already running. Reusing.'
                        } else if (instanceState == 'INSTANCE_INSTALLED_BUT_STOPPED') {
                            echo 'Managed instance stopped. Starting...'
                            bat 'scripts\\batch\\mongodb\\setup\\start_mongodb.bat'
                        } else if (instanceState == 'NO_INSTANCE') {
                            throw new Exception("No managed MongoDB instance found. Run SETUP first to deploy and configure MongoDB. ${instanceError}")
                        } else if (instanceState == 'PORT_OCCUPIED_BY_NON_MONGODB') {
                            throw new Exception("Foreign process detected on MongoDB port. Aborting LOAD to avoid deploying over or reusing an unmanaged listener. ${instanceError}")
                        } else {
                            throw new Exception("Unexpected instance state: ${instanceState}. ${instanceError}")
                        }
                    }
                }
            }
        }


        stage('Validate MongoDB') {

            steps {

                script {

                    runTrackedStage(
                        'Validate MongoDB'
                    ) {

                        bat 'scripts\\batch\\mongodb\\setup\\validate_mongodb.bat'
                    }
                }
            }
        }


        stage('Download Dataset') {

            steps {

                script {

                    runTrackedStage(
                        'Download Dataset'
                    ) {

                        bat 'scripts\\batch\\common\\download_dataset.bat'
                    }
                }
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
        stage('Load Data') {

            steps {

                script {

                    runTrackedStage(
                        'Load Data'
                    ) {

                        bat 'scripts\\batch\\mongodb\\load\\load_data.bat'
                    }
                }
            }
        }


        stage('Validate Loaded Data') {

            steps {

                script {

                    runTrackedStage(
                        'Validate Loaded Data'
                    ) {

                        bat 'scripts\\batch\\mongodb\\load\\validate_loaded_data.bat'
                    }
                }
            }
        }


        /*
        ============================================================
        OPTIONAL POST-PROCESSING
        Assessment/reporting is intentionally not part of CORE LOAD.
        Execute through dedicated assessment/reporting entry point.
        ============================================================
        */


        stage('Database Assessment') {

            when {

                expression {
                    return params.RUN_ASSESSMENT == true
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Database Assessment'
                    ) {

                        bat 'scripts\\batch\\mongodb\\assessment\\run_assessment.bat all'
                    }
                }
            }
        }


        stage('Assessment Report') {

            when {

                expression {
                    return params.RUN_ASSESSMENT == true
                }
            }

            steps {

                script {

                    runTrackedStage(
                        'Assessment Report'
                    ) {

                        bat 'scripts\\batch\\common\\generate_assessment_report.bat'
                    }
                }
            }
        }
    }


    post {

        success {

            echo 'MONGODB LOAD SUCCESSFUL'
        }


        failure {

            echo 'MONGODB LOAD FAILED'
        }


        always {

            echo 'FINALIZING MONGODB LOAD LOGGING AND REPORTING'

            script {

                def finalStatus = currentBuild.currentResult ?: "FAILURE"

                bat """
                    python scripts\\logging\\logger.py finalize ^
                    --database mongodb ^
                    --action load ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --status "${finalStatus}"
                """

                bat """
                    python scripts\\reporting\\generate_report.py ^
                    --database mongodb ^
                    --action load ^
                    --build-number "${env.BUILD_NUMBER}"
                """

                bat """
                    python scripts\\reporting\\generate_history.py ^
                    --database mongodb ^
                    --action load ^
                    --build-number "${env.BUILD_NUMBER}"
                """
            }


            archiveArtifacts(
                artifacts: "logs/mongodb/load/build_${env.BUILD_NUMBER}/**, reports/mongodb/load/build_${env.BUILD_NUMBER}/**, reports/history/**, reports/migration/mongodb/**, outputs/assessments/mongodb/**, outputs/assessments/assessment_report.json, metadata/profiling/mongodb/**, metadata/reconciliation/mongodb/**, metadata/discovery/mongodb/**, metadata/assessment/mongodb/**, metadata/recommendation/mongodb/**, metadata/governance/mongodb/**",
                fingerprint: true,
                allowEmptyArchive: true
            )

            echo 'MONGODB LOAD PIPELINE COMPLETED'
        }
    }
}
