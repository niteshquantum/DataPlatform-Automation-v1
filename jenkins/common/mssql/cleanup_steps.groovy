

def execute(Map context) {
    def runTrackedStage = context.runTrackedStage ?: { String stageName, Closure stageBody -> stageBody() }


        stage('Validate Cleanup Parameters') {


                    runTrackedStage('Validate Cleanup Parameters') {
                        if (
                            params.CLEANUP_MODE != 'PRESERVE_DATA' &&
                            params.CLEANUP_MODE != 'DELETE_DATA'
                        ) {
                            error("Invalid CLEANUP_MODE: ${params.CLEANUP_MODE}")
                        }

                        echo """
=====================================
MSSQL UBUNTU CLEANUP PARAMETERS
=====================================

Cleanup Mode : ${params.CLEANUP_MODE}
"""
                    }
        }

        stage('Run MSSQL Cleanup') {

                    runTrackedStage('Run MSSQL Cleanup') {
                        withEnv([
                            "CLEANUP_MODE=${params.CLEANUP_MODE}"
                        ]) {
                            sh '''
                        echo
                        echo "====================================="
                        echo "RUNNING MSSQL UBUNTU CLEANUP"
                        echo "====================================="
                        echo

                        bash scripts/bash/mssql/cleanup/mssql_cleanup_pipeline.sh

                        echo
                        echo "====================================="
                        echo "MSSQL UBUNTU CLEANUP COMPLETED"
                        echo "====================================="
                        echo
                    '''
                        }
}

return this
