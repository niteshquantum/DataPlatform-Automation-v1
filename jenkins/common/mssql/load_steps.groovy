

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


        stage('Validate Tools') {



                    runTrackedStage('Validate Tools') {

                        sh './scripts/bash/mssql/validate_tools.sh'
                    }
        }


        stage('Start MSSQL') {



                    runTrackedStage('Start MSSQL') {

                        sh './scripts/bash/mssql/setup/start_mssql.sh'
                    }
        }


        stage('Validate MSSQL Instance') {



                    runTrackedStage('Validate MSSQL Instance') {

                        sh './scripts/bash/mssql/setup/validate_mssql_instance.sh'
                    }
        }


        stage('Download Dataset') {



                    runTrackedStage('Download Dataset') {

                        sh './scripts/bash/common/download_dataset.sh'
                    }
        }


        stage('Profile Source Data') {



                    runTrackedStage('Profile Source Data') {

                        sh './scripts/bash/common/run_data_profiling.sh mssql'
                    }
        }
        stage('Schema Detection') {

            runTrackedStage(
                'Schema Detection'
            ) {

                bat 'python scripts\\schema_detector.py mssql'
            }
        }

        stage('Datatype Detection') {

            runTrackedStage(
                'Datatype Detection'
            ) {

                bat 'python scripts\\datatype_registry_generator.py mssql'
            }
        }

        stage('Schema Editor') {

            runTrackedStage(
                'Schema Editor'
            ) {

                bat 'python scripts\\schema_editor\\app.py mssql'
            }
        }

        stage('Create Database') {



                    runTrackedStage('Create Database') {

                        sh './scripts/bash/mssql/setup/create_database.sh'
                    }
        }


        stage('Validate MSSQL') {



                    runTrackedStage('Validate MSSQL') {

                        sh './scripts/bash/mssql/setup/validate_mssql.sh'
                    }
        }


        stage('Load Data') {



                    runTrackedStage('Load Data') {

                        sh './scripts/bash/mssql/load/load_data.sh'
                    }
        }


        stage('Validate Loaded Data') {



                    runTrackedStage('Validate Loaded Data') {

                        sh './scripts/bash/mssql/load/validate_loaded_data.sh'
                    }
        }


        stage('Deploy Database Objects') {



                    runTrackedStage('Deploy Database Objects') {

                        sh './scripts/bash/mssql/objects/deploy_objects.sh'
                    }
        }


        stage('Validate Database Objects') {



                    runTrackedStage('Validate Database Objects') {

                        sh './scripts/bash/mssql/objects/validate_objects.sh'
                    }
        }


        stage('Database Assessment') {



                    runTrackedStage('Database Assessment') {

                        sh './scripts/bash/mssql/assessment/run_assessment.sh all'
                    }
        }


        stage('Assessment Report') {



                    runTrackedStage('Assessment Report') {

                        sh './scripts/bash/common/generate_assessment_report.sh'
                    }
        }


        stage('Reconcile Source and Target Data') {



                    runTrackedStage(
                        'Reconcile Source and Target Data'
                    ) {

                        sh './scripts/bash/common/run_reconciliation.sh mssql'
                    }
        }


        stage('Discover Database Environment') {



                    runTrackedStage(
                        'Discover Database Environment'
                    ) {

                        sh 'python3 scripts/discovery/discovery_engine.py --database mssql'
                    }
        }


        stage('Analyze Database Growth') {



                    runTrackedStage(
                        'Analyze Database Growth'
                    ) {

                        sh 'python3 scripts/discovery/growth_analyzer.py --database mssql'
                    }
        }


        stage('Analyze Migration Requirements') {



                    runTrackedStage(
                        'Analyze Migration Requirements'
                    ) {

                        sh 'python3 scripts/discovery/requirement_analyzer.py --database mssql'
                    }
        }


        stage('Assess Migration') {



                    runTrackedStage('Assess Migration') {

                        sh './scripts/bash/common/run_assessment.sh mssql'
                    }
        }


        stage('Generate Migration Recommendations') {



                    runTrackedStage(
                        'Generate Migration Recommendations'
                    ) {

                        sh './scripts/bash/common/run_recommendation.sh mssql'
                    }
        }


        stage('Generate Governance Action Plan') {



                    runTrackedStage(
                        'Generate Governance Action Plan'
                    ) {

                        sh './scripts/bash/common/run_action_plan.sh mssql'
                    }
        }


        stage('Generate Technical Migration Report') {



                    runTrackedStage(
                        'Generate Technical Migration Report'
                    ) {

                        sh './scripts/bash/common/generate_technical_report.sh mssql'
                    }
        }


        stage('Generate Executive Migration Report') {



                    runTrackedStage(
                        'Generate Executive Migration Report'
                    ) {

                        sh './scripts/bash/common/generate_executive_report.sh mssql'
                    }
                 }
        
        }
return this
