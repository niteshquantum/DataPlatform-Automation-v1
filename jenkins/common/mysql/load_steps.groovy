

def execute(Map context) {
    def runTrackedStage = context.runTrackedStage ?: { String stageName, Closure stageBody -> stageBody() }


        


        stage('Set Permissions') {



                    runTrackedStage('Set Permissions') {

                        sh '''
                            find scripts/bash -type f -name "*.sh" -exec chmod +x {} \\;
                        '''
                    }
        }


        stage('Validate Python Runtime') {



                    runTrackedStage('Validate Python Runtime') {

                        sh './scripts/bash/common/validate_python_runtime.sh'
                    }
        }


        stage('Validate Python Requirements') {



                    runTrackedStage('Validate Python Requirements') {

                        sh './scripts/bash/mysql/setup/validate_python_requirements.sh'
                    }
        }


        stage('Start MySQL') {



                    runTrackedStage('Start MySQL') {

                        sh './scripts/bash/mysql/setup/start_mysql.sh'
                    }
        }


        stage('Validate MySQL Instance') {



                    runTrackedStage('Validate MySQL Instance') {

                        sh './scripts/bash/mysql/setup/validate_mysql_instance.sh'
                    }
        }


        stage('Download Dataset') {



                    runTrackedStage('Download Dataset') {

                        sh './scripts/bash/common/download_dataset.sh'
                    }
        }


        stage('Profile Source Data') {



                    runTrackedStage('Profile Source Data') {

                        sh './scripts/bash/common/run_data_profiling.sh mysql'
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



                    runTrackedStage('Create Database') {

                        sh './scripts/bash/mysql/setup/create_database.sh'
                    }
        }


        stage('Validate MySQL') {



                    runTrackedStage('Validate MySQL') {

                        sh './scripts/bash/mysql/setup/validate_mysql.sh'
                    }
        }


        stage('Load Data') {



                    runTrackedStage('Load Data') {

                        sh './scripts/bash/mysql/load/load_data.sh'
                    }
        }


        stage('Validate Loaded Data') {



                    runTrackedStage('Validate Loaded Data') {

                        sh './scripts/bash/mysql/load/validate_loaded_data.sh'
                    }
        }


        stage('Deploy Database Objects') {



                    runTrackedStage('Deploy Database Objects') {

                        sh './scripts/bash/mysql/objects/deploy_objects.sh'
                    }
        }


        stage('Validate Database Objects') {



                    runTrackedStage('Validate Database Objects') {

                        sh './scripts/bash/mysql/objects/validate_objects.sh'
                    }
        }


        stage('Database Assessment') {



                    runTrackedStage('Database Assessment') {

                        sh './scripts/bash/mysql/assessment/run_assessment.sh all'
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

                        sh './scripts/bash/common/run_reconciliation.sh mysql'
                    }
        }


        stage('Discover Database Environment') {



                    runTrackedStage(
                        'Discover Database Environment'
                    ) {

                        sh 'python3 scripts/discovery/discovery_engine.py --database mysql'
                    }
        }


        stage('Analyze Database Growth') {



                    runTrackedStage(
                        'Analyze Database Growth'
                    ) {

                        sh 'python3 scripts/discovery/growth_analyzer.py --database mysql'
                    }
        }


        stage('Analyze Migration Requirements') {



                    runTrackedStage(
                        'Analyze Migration Requirements'
                    ) {

                        sh 'python3 scripts/discovery/requirement_analyzer.py --database mysql'
                    }
        }


        stage('Assess Migration') {



                    runTrackedStage('Assess Migration') {

                        sh './scripts/bash/common/run_assessment.sh mysql'
                    }
        }


        stage('Generate Migration Recommendations') {



                    runTrackedStage(
                        'Generate Migration Recommendations'
                    ) {

                        sh './scripts/bash/common/run_recommendation.sh mysql'
                    }
        }


        stage('Generate Governance Action Plan') {



                    runTrackedStage(
                        'Generate Governance Action Plan'
                    ) {

                        sh './scripts/bash/common/run_action_plan.sh mysql'
                    }
        }


        stage('Generate Technical Migration Report') {



                    runTrackedStage(
                        'Generate Technical Migration Report'
                    ) {

                        sh './scripts/bash/common/generate_technical_report.sh mysql'
                    }
        }


       stage('Generate Executive Migration Report') {

    runTrackedStage(
        'Generate Executive Migration Report'
    ) {

        sh './scripts/bash/common/generate_executive_report.sh mysql'
    }
}

}

return this
