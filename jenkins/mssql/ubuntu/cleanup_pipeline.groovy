def context = [database: 'mssql', action: 'cleanup', operatingSystem: 'ubuntu']
pipeline {
    agent { label 'ubuntu-node' }
    parameters { choice(name: 'CLEANUP_MODE', choices: ['PRESERVE_DATA', 'DELETE_DATA', 'RESET_SCHEMA_CONTEXT'], description: 'Select MSSQL cleanup mode') }
    stages {
        stage('Initialize Logging') { steps { script { load('jenkins/common/standalone_pipeline_support.groovy').initialize(context) } } }
        stage('Execute MSSQL CLEANUP Steps') { steps { script { def tracker = load 'jenkins/common/common_stage_tracker.groovy'; load('jenkins/common/mssql/cleanup_steps.groovy').execute(context + [runTrackedStage: { String stageName, Closure stageBody -> tracker.track(context, stageName, stageBody) }]) } } }
    }
    post {
        success { echo 'UBUNTU MSSQL CLEANUP SUCCESSFUL' }
        failure { echo 'UBUNTU MSSQL CLEANUP FAILED' }
        always { script { load('jenkins/common/standalone_pipeline_support.groovy').finalize(context) }; echo 'UBUNTU MSSQL CLEANUP PIPELINE COMPLETED' }
    }
}
