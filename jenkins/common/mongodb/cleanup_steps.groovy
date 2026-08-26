

def execute(Map context) {
    def runTrackedStage = context.runTrackedStage ?: { String stageName, Closure stageBody -> stageBody() }



        stage('Validate Cleanup Parameters') {

                    runTrackedStage('Validate Cleanup Parameters') {
                        if (
                            params.CLEANUP_MODE != 'PRESERVE_DATA' &&
                            params.CLEANUP_MODE != 'DELETE_DATA' &&
                            params.CLEANUP_MODE != 'RESET_SCHEMA_CONTEXT'
                        ) {
                            error("Invalid CLEANUP_MODE: ${params.CLEANUP_MODE}")
                        }
                    }
        }

        stage('Run MongoDB Cleanup') {

                    runTrackedStage('Run MongoDB Cleanup') {
                        withEnv([
                            "CLEANUP_MODE=${params.CLEANUP_MODE}"
                        ]) {
                            bat 'scripts\\batch\\mongodb\\cleanup\\mongodb_cleanup_pipeline.bat'
                        }
                    }
        }
}

return this
