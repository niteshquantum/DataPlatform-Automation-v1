MASTER_HEADER = """<?xml version="1.0" encoding="UTF-8"?>

<databaseChangeLog

    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"

    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"

    xsi:schemaLocation="

    http://www.liquibase.org/xml/ns/dbchangelog

    http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.20.xsd">
"""

MASTER_FOOTER = """

</databaseChangeLog>
"""

MASTER_INCLUDE = """
    <include file="{file}" relativeToChangelogFile="true"/>
"""