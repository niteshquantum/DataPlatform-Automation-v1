

def execute(Map context) {
    def runTrackedStage = context.runTrackedStage ?: { String stageName, Closure stageBody -> stageBody() }


        


        stage('Run PostgreSQL Cleanup') {

                    runTrackedStage('Run PostgreSQL Cleanup') {
                        withEnv([
                            "CLEANUP_MODE=${params.CLEANUP_MODE}"
                        ]) {
                            bat 'scripts\\batch\\postgresql\\cleanup\\postgresql_cleanup_pipeline.bat'
                        }
}

return this
