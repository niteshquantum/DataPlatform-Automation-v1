def track(Map c, String n, Closure body) {
    def start = c.operatingSystem == 'windows' ? "python scripts\\logging\\logger.py stage-start ^\n--database ${c.database} ^\n--action ${c.action} ^\n--build-number \"${env.BUILD_NUMBER}\" ^\n--stage-name \"${n}\"" : "python3 scripts/logging/logger.py stage-start \\\n--database ${c.database} \\\n--action ${c.action} \\\n--build-number \"${env.BUILD_NUMBER}\" \\\n--stage-name \"${n}\""
    if (c.operatingSystem == 'windows') { bat start } else { sh start }
    try {
        body()
        def end = c.operatingSystem == 'windows' ? "python scripts\\logging\\logger.py stage-end ^\n--database ${c.database} ^\n--action ${c.action} ^\n--build-number \"${env.BUILD_NUMBER}\" ^\n--stage-name \"${n}\" ^\n--status SUCCESS" : "python3 scripts/logging/logger.py stage-end \\\n--database ${c.database} \\\n--action ${c.action} \\\n--build-number \"${env.BUILD_NUMBER}\" \\\n--stage-name \"${n}\" \\\n--status SUCCESS"
        if (c.operatingSystem == 'windows') { bat end } else { sh end }
    } catch (Exception e) {
        def end = c.operatingSystem == 'windows' ? "python scripts\\logging\\logger.py stage-end ^\n--database ${c.database} ^\n--action ${c.action} ^\n--build-number \"${env.BUILD_NUMBER}\" ^\n--stage-name \"${n}\" ^\n--status FAILURE" : "python3 scripts/logging/logger.py stage-end \\\n--database ${c.database} \\\n--action ${c.action} \\\n--build-number \"${env.BUILD_NUMBER}\" \\\n--stage-name \"${n}\" \\\n--status FAILURE"
        def error = c.operatingSystem == 'windows' ? "python scripts\\logging\\logger.py set-error ^\n--database ${c.database} ^\n--action ${c.action} ^\n--build-number \"${env.BUILD_NUMBER}\" ^\n--failed-stage \"${n}\" ^\n--message \"Stage execution failed\"" : "python3 scripts/logging/logger.py set-error \\\n--database ${c.database} \\\n--action ${c.action} \\\n--build-number \"${env.BUILD_NUMBER}\" \\\n--failed-stage \"${n}\" \\\n--message \"Stage execution failed\""
        if (c.operatingSystem == 'windows') { bat end; bat error } else { sh end; sh error }
        throw e
    }
}
return this