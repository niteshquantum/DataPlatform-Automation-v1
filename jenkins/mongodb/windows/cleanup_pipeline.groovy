def context = [database: 'mongodb', action: 'cleanup', operatingSystem: 'windows']
pipeline {
    agent { label 'windows-node' }
    parameters { choice(name: 'CLEANUP_MODE', choices: ['PRESERVE_DATA', 'DELETE_DATA'], description: 'Select cleanup mode') }
    stages {
        stage('Initialize Logging') { steps { script { load('jenkins/common/standalone_pipeline_support.groovy').initialize(context) } } }
        stage('Execute MONGODB CLEANUP Steps') { steps { script { def tracker = load 'jenkins/common/common_stage_tracker.groovy'; load('jenkins/common/mongodb/cleanup_steps.groovy').execute(context + [runTrackedStage: { String stageName, Closure stageBody -> tracker.track(context, stageName, stageBody) }]) } } }
    }
    post {
        success { echo 'WINDOWS MONGODB CLEANUP SUCCESSFUL' }
        failure { echo 'WINDOWS MONGODB CLEANUP FAILED' }
        always { script { load('jenkins/common/standalone_pipeline_support.groovy').finalize(context) }; echo 'WINDOWS MONGODB CLEANUP PIPELINE COMPLETED' }
    }
}
