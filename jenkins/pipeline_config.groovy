/*
 * Single source of truth for database pipeline routing.
 */

def pipelineRoutes = [
    MYSQL: [
        SETUP  : [node: 'ubuntu-node',  os: 'ubuntu',  path: 'jenkins/common/mysql/setup_steps.groovy'],
        LOAD   : [node: 'ubuntu-node',  os: 'ubuntu',  path: 'jenkins/common/mysql/load_steps.groovy'],
        CLEANUP: [node: 'ubuntu-node',  os: 'ubuntu',  path: 'jenkins/common/mysql/cleanup_steps.groovy']
    ],

    POSTGRESQL: [
        SETUP  : [node: 'windows-node', os: 'windows', path: 'jenkins/common/postgresql/setup_steps.groovy'],
        LOAD   : [node: 'windows-node', os: 'windows', path: 'jenkins/common/postgresql/load_steps.groovy'],
        CLEANUP: [node: 'windows-node', os: 'windows', path: 'jenkins/common/postgresql/cleanup_steps.groovy']
    ],

    MONGODB: [
        SETUP  : [node: 'windows-node', os: 'windows', path: 'jenkins/common/mongodb/setup_steps.groovy'],
        LOAD   : [node: 'windows-node', os: 'windows', path: 'jenkins/common/mongodb/load_steps.groovy'],
        CLEANUP: [node: 'windows-node', os: 'windows', path: 'jenkins/common/mongodb/cleanup_steps.groovy']
    ],

    MSSQL: [
        SETUP  : [node: 'ubuntu-node',  os: 'ubuntu',  path: 'jenkins/common/mssql/setup_steps.groovy'],
        LOAD   : [node: 'ubuntu-node',  os: 'ubuntu',  path: 'jenkins/common/mssql/load_steps.groovy'],
        CLEANUP: [node: 'ubuntu-node',  os: 'ubuntu',  path: 'jenkins/common/mssql/cleanup_steps.groovy']
    ]
]

return [
    resolve: { database, action ->

        def db = database?.toUpperCase()
        def act = action?.toUpperCase()

        def route = pipelineRoutes[db]?.get(act)

        if (!route) {
            error("Unsupported pipeline selection: DATABASE=${database}, ACTION=${action}")
        }

        return route.asImmutable()
    }
]