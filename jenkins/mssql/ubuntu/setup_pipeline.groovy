def context = [database: 'mssql', action: 'setup', operatingSystem: 'ubuntu']
pipeline {
    agent { label 'ubuntu-node' }
    stages {
        stage('Initialize Logging') { steps { script { load('jenkins/common/standalone_pipeline_support.groovy').initialize(context) } } }
        stage('Execute MSSQL SETUP Steps') { steps { script { def tracker = load 'jenkins/common/common_stage_tracker.groovy'; load('jenkins/common/mssql/setup_steps.groovy').execute(context + [runTrackedStage: { String stageName, Closure stageBody -> tracker.track(context, stageName, stageBody) }]) } } }
    }
    post {
        success { echo 'UBUNTU MSSQL SETUP SUCCESSFUL' }
        failure { echo 'UBUNTU MSSQL SETUP FAILED' }
        always { script { load('jenkins/common/standalone_pipeline_support.groovy').finalize(context) }; echo 'UBUNTU MSSQL SETUP PIPELINE COMPLETED' }
    }
}
