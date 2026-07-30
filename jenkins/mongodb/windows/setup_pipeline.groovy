def context = [database: 'mongodb', action: 'setup', operatingSystem: 'windows']
pipeline {
    agent { label 'windows-node' }
    stages {
        stage('Initialize Logging') { steps { script { load('jenkins/common/standalone_pipeline_support.groovy').initialize(context) } } }
        stage('Execute MONGODB SETUP Steps') { steps { script { def tracker = load 'jenkins/common/common_stage_tracker.groovy'; load('jenkins/common/mongodb/setup_steps.groovy').execute(context + [runTrackedStage: { String stageName, Closure stageBody -> tracker.track(context, stageName, stageBody) }]) } } }
    }
    post {
        success { echo 'WINDOWS MONGODB SETUP SUCCESSFUL' }
        failure { echo 'WINDOWS MONGODB SETUP FAILED' }
        always { script { load('jenkins/common/standalone_pipeline_support.groovy').finalize(context) }; echo 'WINDOWS MONGODB SETUP PIPELINE COMPLETED' }
    }
}
