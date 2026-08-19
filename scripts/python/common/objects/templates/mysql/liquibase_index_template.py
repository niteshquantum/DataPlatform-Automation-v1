LIQUIBASE_INDEX_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>

<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="
        http://www.liquibase.org/xml/ns/dbchangelog
        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.20.xsd">

    <changeSet id="mysql-{id}-v3" author="automation">

        <preConditions onFail="MARK_RAN" onError="HALT">
            <sqlCheck expectedResult="0">
                SELECT COUNT(*)
                FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = '{table_name_sql}'
                  AND INDEX_NAME = '{index_name_sql}'
            </sqlCheck>
        </preConditions>

        <sql>
            CREATE INDEX `{index_name_sql_identifier}`
            ON `{table_name_sql_identifier}` ({column_names_sql});
        </sql>

    </changeSet>

</databaseChangeLog>
"""