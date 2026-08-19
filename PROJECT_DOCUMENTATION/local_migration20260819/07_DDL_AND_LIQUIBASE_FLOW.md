# DDL and Liquibase Flow

## What This Covers

How extracted schema metadata is converted into Liquibase XML changelogs, how `master.xml` is maintained, and how Liquibase applies the changelog to the destination database.

## Stage 5: Generate Target DDL

**Batch wrapper:** `scripts/batch/migration/windows/generate_ddl.bat`
**Python module:** `scripts/python/migration/generate_ddl.py`

### What It Does

1. Resolves effective destination configuration to determine the destination database type.
2. Reads `metadata/<database>/schema_registry.json`.
3. Compares existing Liquibase XML files against the registry to detect new tables or new columns.
4. Generates Liquibase XML changelog files into `liquibase/migration/<database>/`.
5. Updates `master.xml` to include all generated changelog files.
6. Writes `schema_status.json` to indicate whether any schema changes were detected.

### Generated File Naming Convention

Files are numbered sequentially and named based on the operation:

| Scenario | Filename Pattern | Example |
|----------|-----------------|---------|
| New table | `{NNN}_create_{table_name}.xml` | `001_create_customers.xml` |
| Existing table with new columns | `{NNN}_alter_{table_name}_add_columns.xml` | `004_alter_customers_add_columns.xml` |

NNN is a zero-padded 3-digit sequence number starting from the count of existing XML files + 1.

### XML Structure

#### Create Table Changeset

```xml
<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog
        xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
        xmlns:xsi="http://www.w3.org/XMLSchema-instance"
        xsi:schemaLocation="
        http://www.liquibase.org/xml/ns/dbchangelog
        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

    <changeSet id="001" author="tanisha">

    <preConditions onFail="MARK_RAN">
        <not>
            <tableExists tableName="customers"/>
        </not>
    </preConditions>

    <createTable tableName="customers">
        <column name="customer_id" type="VARCHAR(255)"/>
        <column name="customer_name" type="VARCHAR(255)"/>
    </createTable>

    </changeSet>

</databaseChangeLog>
```

#### Alter Table (Add Column) Changeset

```xml
<?xml version="1.0" encoding="UTF-8"?>
<databaseChangeLog
        xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
        xmlns:xsi="http://www.w3.org/XMLSchema-instance"
        xsi:schemaLocation="
        http://www.liquibase.org/xml/ns/dbchangelog
        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">

    <changeSet id="004" author="tanisha">

    <preConditions onFail="MARK_RAN">
        <and>
            <not>
                <columnExists tableName="customers" columnName="phone_number"/>
            </not>
        </and>
    </preConditions>

    <addColumn tableName="customers">
        <column name="phone_number" type="VARCHAR(255)"/>
    </addColumn>

    </changeSet>

</databaseChangeLog>
```

### Preconditions

- `onFail="MARK_RAN"` — if the precondition check fails (e.g., table already exists), Liquibase marks the changeset as ran without executing it. This makes the pipeline idempotent.
- For `createTable`: precondition checks that the table does NOT exist.
- For `addColumn`: precondition checks that each new column does NOT exist.

### master.xml

`master.xml` is regenerated on every DDL generation run. It includes all XML files in the migration directory (excluding itself):

```xml
<?xml version="1.0" encoding="utf-8"?>
<databaseChangeLog xmlns="http://www.liquibase.org/xml/ns/dbchangelog"
        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
        xsi:schemaLocation="http://www.liquibase.org/xml/ns/dbchangelog
        http://www.liquibase.org/xml/ns/dbchangelog/dbchangelog-latest.xsd">
<include file="001_create_customers.xml" relativeToChangelogFile="true" />
<include file="002_create_orders.xml" relativeToChangelogFile="true" />
<include file="003_create_products.xml" relativeToChangelogFile="true" />
<include file="004_alter_customers_add_columns.xml" relativeToChangelogFile="true" />
<include file="master_objects.xml" relativeToChangelogFile="true" />
</databaseChangeLog>
```

### Idempotency in DDL Generation

The generator compares existing XML files against the schema registry. If no new tables or columns are detected, it prints:

```
No schema changes detected. Nothing to generate.
```

It does not delete or modify existing changelog files. This means re-running extraction on an unchanged source produces no new DDL.

## Stage 6: Install Liquibase and Drivers

These are **runtime preparation stages**, not separate migration logic.

### Install Liquibase

**Batch wrapper:** `scripts/batch/common/install_liquibase.bat`

Downloads Liquibase if not already present under `tools/liquibase/`. If Liquibase already exists, the stage reports "Liquibase already exists."

### Install Drivers

Three driver installation scripts run sequentially:

| Script | Driver | File Pattern |
|--------|--------|-------------|
| `scripts/batch/common/install_mssql_driver.bat` | MSSQL JDBC | `tools/drivers/mssql-jdbc-<version>.jre11.jar` |
| `scripts/batch/mysql/setup/install_mysql_driver.bat` | MySQL Connector/J | `tools/drivers/mysql-connector-j-<version>.jar` |
| `scripts/batch/postgresql/setup/install_postgresql_driver.bat` | PostgreSQL JDBC | `tools/drivers/postgresql-<version>.jar` |

Drivers are downloaded via PowerShell scripts if not already present. The stage reports "already installed" when the driver file exists.

## Stage 7: Apply Schema

**Batch wrapper:** `scripts/batch/migration/windows/apply_schema.bat`
**Python module:** `scripts/python/migration/apply_schema.py`
**Liquibase runner:** `scripts/batch/migration/windows/run_liquibase.bat`

### What It Does

1. Resolves effective destination configuration.
2. Locates the migration changelog: `liquibase/migration/<database>/master.xml`.
3. Invokes `run_liquibase.bat` with database type, changelog path, command (`update`), and connection parameters.
4. `run_liquibase.bat`:
   - Reads migration config for the destination database type.
   - Overrides config values with explicit arguments if provided.
   - Validates Liquibase installation and version.
   - Validates the correct JDBC driver exists.
   - Constructs the JDBC URL for the destination database type.
   - Executes Liquibase with the appropriate driver class and URL.

### Liquibase Execution Details

| Database | JDBC URL Pattern | Driver Class |
|----------|-----------------|-------------|
| MSSQL | `jdbc:sqlserver://<host>:<port>;databaseName=<db>;encrypt=true;trustServerCertificate=true` | `com.microsoft.sqlserver.jdbc.SQLServerDriver` |
| MySQL | `jdbc:mysql://<host>:<port>/<db>` | `com.mysql.cj.jdbc.Driver` |
| PostgreSQL | `jdbc:postgresql://<host>:<port>/<db>` | `org.postgresql.Driver` |

### Liquibase Command

```bash
liquibase.bat ^
    --classpath="<driver.jar>" ^
    --driver="<driver_class>" ^
    --search-path="<project_root>" ^
    --changeLogFile="liquibase/migration/<db>/master.xml" ^
    --url="<jdbc_url>" ^
    --username=<user> ^
    --password=<password> ^
    update
```

### Runtime Validation

Before running Liquibase, `run_liquibase.bat` validates:
1. Liquibase executable exists at `tools/liquibase/liquibase.bat`
2. Liquibase version matches expected version (e.g., `5.0.3`)
3. Java is installed and `JAVA_HOME` is set
4. JDBC driver file exists at `tools/drivers/`
5. Changelog file exists at the specified path

## Liquibase Directory Structure After Migration

```
liquibase/
  migration/
    mysql/
      master.xml
      master_objects.xml
      001_create_customers.xml
      002_create_orders.xml
      003_create_products.xml
      004_alter_customers_add_columns.xml
```

`master_objects.xml` is created as an empty placeholder if it does not exist. It is included in `master.xml` but is not a migration changeset.

## Liquibase Isolation

Production Liquibase directories remain completely separate:

```
liquibase/
  mysql/              ← PRODUCTION (untouched by migration)
  mssql/              ← PRODUCTION (untouched by migration)
  postgresql/         ← PRODUCTION (untouched by migration)
  migration/
    mysql/            ← MIGRATION OUTPUT
    mssql/            ← MIGRATION OUTPUT
    postgresql/       ← MIGRATION OUTPUT
```

This isolation prevents checksum mismatches and production contamination during testing.
