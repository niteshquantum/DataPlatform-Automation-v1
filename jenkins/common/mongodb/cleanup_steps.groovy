

def execute(Map context) {
    def runTrackedStage = context.runTrackedStage ?: { String stageName, Closure stageBody -> stageBody() }


        


        stage('Run MongoDB Cleanup') {

                    runTrackedStage('Run MongoDB Cleanup') {
                        withEnv([
                            "CLEANUP_MODE=${params.CLEANUP_MODE}"
                        ]) {
                            bat 'scripts\\batch\\mongodb\\cleanup\\mongodb_cleanup_pipeline.bat'
                        }
}

return this
