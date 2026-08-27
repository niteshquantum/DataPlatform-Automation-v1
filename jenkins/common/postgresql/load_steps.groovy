

def execute(Map context) {
    def runTrackedStage = context.runTrackedStage ?: { String stageName, Closure stageBody -> stageBody() }


        


        stage('Validate Python Runtime') {



                    runTrackedStage(
                        'Validate Python Runtime'
                    ) {

                        bat 'scripts\\batch\\common\\validate_python_runtime.bat'
                    }
        }


        stage('Validate PostgreSQL Requirements') {



                    runTrackedStage(
                        'Validate PostgreSQL Requirements'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\validate_python_requirements.bat'
                    }
        }


        stage('Install Tools') {



                    runTrackedStage(
                        'Install Tools'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\install_tools.bat'
                    }
        }


        stage('Validate Tools') {



                    runTrackedStage(
                        'Validate Tools'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\validate_tools.bat'
                    }
        }


        stage('Start PostgreSQL') {



                    runTrackedStage(
                        'Start PostgreSQL'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\start_postgresql.bat'
                    }
        }


        stage('Validate PostgreSQL Instance') {



                    runTrackedStage(
                        'Validate PostgreSQL Instance'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\validate_postgresql.bat'
                    }
        }


        stage('Download Dataset') {

            runTrackedStage(
                'Download Dataset'
            ) {

                withEnv([
                    "SOURCE_TYPE=${context.sourceType}",
                    "SOURCE_PATH=${context.sourcePath}",
                    "FORCE_DOWNLOAD=${context.forceDownload}"
                ]) {

                    bat 'scripts\\batch\\common\\download_dataset.bat'
                }
            }
        }


        stage('Verify Download') {

            runTrackedStage(
                'Verify Download'
            ) {

                bat 'python scripts\\python\\common\\verify_download.py'
            }
        }

        stage('Profile Source Data') {



                    runTrackedStage(
                        'Profile Source Data'
                    ) {

                        bat 'python scripts\\profiling\\data_profiler.py --database postgresql'
                    }
        }

        stage('Schema Detection') {

            runTrackedStage('Schema Detection') {

                bat 'python scripts\\schema_detector.py postgresql'

            }
        }

        stage('Datatype Detection') {

            runTrackedStage('Datatype Detection') {

                bat 'python scripts\\datatype_registry_generator.py postgresql'

            }
        }

        stage('Schema Editor') {

            runTrackedStage('Schema Editor') {

                bat 'python scripts\\schema_editor\\app.py postgresql'

            }
        }
        stage('Create Database') {



                    runTrackedStage(
                        'Create Database'
                    ) {

                        bat 'scripts\\batch\\postgresql\\setup\\create_database.bat'
                    }
        }


        stage('Run CDC') {



                    bat """
                        python scripts\\logging\\logger.py stage-start ^
                        --database postgresql ^
                        --action load ^
                        --build-number "${env.BUILD_NUMBER}" ^
                        --stage-name "Run CDC"
                    """

                    def cdcResult = bat(
                        script: 'scripts\\batch\\postgresql\\load\\run_cdc.bat',
                        returnStatus: true
                    )

                    if (cdcResult == 0 || cdcResult == 100) {
                        bat """
                            python scripts\\logging\\logger.py stage-end ^
                            --database postgresql ^
                            --action load ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --stage-name "Run CDC" ^
                            --status SUCCESS
                        """
                        if (cdcResult == 100) {
                            env.SKIP_DATA_LOAD = 'true'
                        }
                    } else {
                        bat """
                            python scripts\\logging\\logger.py stage-end ^
                            --database postgresql ^
                            --action load ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --stage-name "Run CDC" ^
                            --status FAILURE
                        """
                        bat """
                            python scripts\\logging\\logger.py set-error ^
                            --database postgresql ^
                            --action load ^
                            --build-number "${env.BUILD_NUMBER}" ^
                            --failed-stage "Run CDC" ^
                            --message "CDC execution failed with exit code ${cdcResult}"
                        """
                        error "CDC execution failed with exit code ${cdcResult}"
                    }
        }


        if ({ -> return env.SKIP_DATA_LOAD != 'true' }()) {
            stage('Load Data') {runTrackedStage(
                        'Load Data'
                    ) {

                        bat 'scripts\\batch\\postgresql\\load\\load_data.bat'
                    }
            }
        }


        if ({ -> return env.SKIP_DATA_LOAD != 'true' }()) {
            stage('Validate Loaded Data') {runTrackedStage(
                        'Validate Loaded Data'
                    ) {

                        bat 'scripts\\batch\\postgresql\\load\\validate_loaded_data.bat'
                    }
                }
        }


        stage('Deploy Database Objects') {



                    runTrackedStage(
                        'Deploy Database Objects'
                    ) {

                        bat 'scripts\\batch\\postgresql\\objects\\deploy_objects.bat'
                    }
        }


        stage('Validate Database Objects') {



                    runTrackedStage(
                        'Validate Database Objects'
                    ) {

                        bat 'scripts\\batch\\postgresql\\objects\\validate_objects.bat'
                    }
        }


        stage('Assessment & Reconciliation') {



                    runTrackedStage(
                        'Assessment & Reconciliation'
                    ) {

                        bat 'scripts\\batch\\postgresql\\assessment\\run_assessment_pipeline.bat'
                    }
        }


        stage('Discovery & Migration Reporting') {



                    runTrackedStage(
                        'Discovery & Migration Reporting'
                    ) {

                        bat 'scripts\\batch\\postgresql\\migration\\run_migration_pipeline.bat'
                
                }
        }
    }
return this
