def context = [database: 'postgresql', action: 'load', operatingSystem: 'windows']
pipeline {
    agent { label 'windows-node' }
    stages {
        stage('Initialize Logging') { steps { script { load('jenkins/common/standalone_pipeline_support.groovy').initialize(context) } } }
        stage('Execute POSTGRESQL LOAD Steps') { steps { script { def tracker = load 'jenkins/common/common_stage_tracker.groovy'; load('jenkins/common/postgresql/load_steps.groovy').execute(context + [runTrackedStage: { String stageName, Closure stageBody -> tracker.track(context, stageName, stageBody) }]) } } }
    }
    post {
        success { echo 'WINDOWS POSTGRESQL LOAD SUCCESSFUL' }
        failure { echo 'WINDOWS POSTGRESQL LOAD FAILED' }
        always { script { load('jenkins/common/standalone_pipeline_support.groovy').finalize(context) }; echo 'WINDOWS POSTGRESQL LOAD PIPELINE COMPLETED' }
    }
}
