/*
 * Standalone lifecycle counterpart to executePipeline() in Jenkinsfile.
 * RBAC remains master-only; all applicable logging/reporting behaviour is
 * intentionally kept equivalent here.
 */
def initialize(Map context) {
    if (context.operatingSystem == 'windows') {
        bat """
            python scripts\\logging\\logger.py init ^
                --database "${context.database}" ^
                --action "${context.action}" ^
                --os "${context.operatingSystem}" ^
                --build-number "${env.BUILD_NUMBER}" ^
                --job-name "${env.JOB_NAME}" ^
                --build-url "${env.BUILD_URL}"
        """
    } else {
        sh """
            python3 scripts/logging/logger.py init \\
                --database "${context.database}" \\
                --action "${context.action}" \\
                --os "${context.operatingSystem}" \\
                --build-number "${env.BUILD_NUMBER}" \\
                --job-name "${env.JOB_NAME}" \\
                --build-url "${env.BUILD_URL}"
        """
    }

    context.loggingInitialized = true
}

def finalize(Map context) {
    if (!context.loggingInitialized) {
        return
    }

    def finalStatus = currentBuild.currentResult ?: 'FAILURE'

    try {
        if (context.operatingSystem == 'windows') {
            bat """
                python scripts\\logging\\logger.py finalize ^
                    --database "${context.database}" ^
                    --action "${context.action}" ^
                    --build-number "${env.BUILD_NUMBER}" ^
                    --status "${finalStatus}"
            """
        } else {
            sh """
                python3 scripts/logging/logger.py finalize \\
                    --database "${context.database}" \\
                    --action "${context.action}" \\
                    --build-number "${env.BUILD_NUMBER}" \\
                    --status "${finalStatus}"
            """
        }
    } catch (Exception finalizeError) {
        echo "WARNING: Logging finalization failed: ${finalizeError}"
    }

    try {
        if (context.operatingSystem == 'windows') {
            bat """
                python scripts\\reporting\\generate_report.py ^
                    --database "${context.database}" ^
                    --action "${context.action}" ^
                    --build-number "${env.BUILD_NUMBER}"
            """
            bat """
                python scripts\\reporting\\generate_history.py ^
                    --database "${context.database}" ^
                    --action "${context.action}" ^
                    --build-number "${env.BUILD_NUMBER}"
            """
        } else {
            sh """
                python3 scripts/reporting/generate_report.py \\
                    --database "${context.database}" \\
                    --action "${context.action}" \\
                    --build-number "${env.BUILD_NUMBER}"
            """
            sh """
                python3 scripts/reporting/generate_history.py \\
                    --database "${context.database}" \\
                    --action "${context.action}" \\
                    --build-number "${env.BUILD_NUMBER}"
            """
        }
    } catch (Exception reportError) {
        echo "WARNING: Report generation failed: ${reportError}"
    }

    try {
        archiveArtifacts(
            artifacts:
                "logs/${context.database}/${context.action}/build_${env.BUILD_NUMBER}/**," +
                "reports/${context.database}/${context.action}/build_${env.BUILD_NUMBER}/**," +
                "reports/history/**," +
                "reports/migration/${context.database}/**," +
                "outputs/assessments/${context.database}/**," +
                "outputs/assessments/assessment_report.json," +
                "metadata/profiling/${context.database}/**," +
                "metadata/reconciliation/${context.database}/**," +
                "metadata/discovery/${context.database}/**," +
                "metadata/assessment/${context.database}/**," +
                "metadata/recommendation/${context.database}/**," +
                "metadata/governance/${context.database}/**",
            fingerprint: true,
            allowEmptyArchive: true
        )
        publishHTML([
            allowMissing: true,
            alwaysLinkToLastBuild: true,
            keepAll: true,
            reportDir: "reports/migration/${context.database}",
            reportFiles: 'executive_report.html',
            reportName: "${context.database.toUpperCase()} Executive Report"
        ])
    } catch (Exception archiveError) {
        echo "WARNING: Artifact archiving failed: ${archiveError}"
    }
}

return this
