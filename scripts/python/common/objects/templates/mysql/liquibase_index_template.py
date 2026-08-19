LIQUIBASE_INDEX_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>

<databaseChangeLog
    xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="
        http://www.liquibase.org/xml/ns/dbchangelog
        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-4.20.xsd">

    <changeSet id="{id}" author="automation">

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
            SET @automation_index_sql = (
                SELECT CASE
                    WHEN COUNT(*) = 0 THEN
                        CONCAT(
                            'CREATE INDEX `',
                            '{index_name_sql_identifier}',
                            '` ON `',
                            '{table_name_sql_identifier}',
                            '` (',
                            GROUP_CONCAT(
                                CASE
                                    WHEN UPPER(c.DATA_TYPE) IN (
                                        'TINYTEXT',
                                        'TEXT',
                                        'MEDIUMTEXT',
                                        'LONGTEXT',
                                        'TINYBLOB',
                                        'BLOB',
                                        'MEDIUMBLOB',
                                        'LONGBLOB'
                                    )
                                    THEN CONCAT(
                                        '`',
                                        REPLACE(s.COLUMN_NAME, '`', '``'),
                                        '`(255)'
                                    )
                                    ELSE CONCAT(
                                        '`',
                                        REPLACE(s.COLUMN_NAME, '`', '``'),
                                        '`'
                                    )
                                END
                                ORDER BY s.SEQ_IN_INDEX
                                SEPARATOR ', '
                            ),
                            ')'
                        )
                    ELSE
                        'SELECT 1'
                END
                FROM information_schema.STATISTICS s
                INNER JOIN information_schema.COLUMNS c
                    ON c.TABLE_SCHEMA = s.TABLE_SCHEMA
                   AND c.TABLE_NAME = s.TABLE_NAME
                   AND c.COLUMN_NAME = s.COLUMN_NAME
                WHERE s.TABLE_SCHEMA = DATABASE()
                  AND s.TABLE_NAME = '{table_name_sql}'
                  AND s.INDEX_NAME = '{index_name_sql}'
            );

            SET @automation_index_sql = COALESCE(
                @automation_index_sql,
                'SELECT 1'
            );

            PREPARE automation_index_stmt
                FROM @automation_index_sql;

            EXECUTE automation_index_stmt;

            DEALLOCATE PREPARE automation_index_stmt;
        </sql>

    </changeSet>

</databaseChangeLog>
"""