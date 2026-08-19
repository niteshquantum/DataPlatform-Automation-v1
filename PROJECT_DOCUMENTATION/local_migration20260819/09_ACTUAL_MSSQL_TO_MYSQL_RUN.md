# Actual MSSQL to MySQL Run

## What This Covers

A complete walkthrough of the actual test run documented in `jenkins_testing/outputs/#4 (1).txt`, showing every stage, its output, and what it means.

## Run Identity

| Attribute | Value |
|-----------|-------|
| Triggered by | `Nitesh Patel` |
| Jenkins workspace | `C:\Users\Admin\.jenkins\workspace\001_mig_shema_extrat` |
| Git branch | `feature/jenkins-dataset-source-links` |
| Commit | `4cbdba8fb37a5683d064016cefda9f4b4d5a2d8f` |
| Commit message | `update jekin` |
| Source repository | `https://github.com/niteshquantum/DataPlatform-Automation-v1.git` |
| Final result | `SUCCESS` |

## Jenkins Parameters Used

```
SOURCE_DATABASE      = MSSQL
SOURCE_HOST          = localhost
SOURCE_PORT          = 1533
SOURCE_DB            = ecommerce_mssql
SOURCE_SCHEMA        = dbo
SOURCE_USER          = sa
SOURCE_PASSWORD      = ********

DESTINATION_DATABASE = MYSQL
DESTINATION_HOST     = 127.0.0.1
DESTINATION_PORT     = 3306
DESTINATION_DB       = test_schema_1
DESTINATION_SCHEMA   = (empty)
DESTINATION_USER     = rootuser
DESTINATION_PASSWORD = ********
```

Note: `DESTINATION_SCHEMA` is empty, which is expected behavior for MySQL (MySQL does not have a schema concept equivalent to MSSQL/PostgreSQL; schema validation always passes for MySQL).

## Effective Configuration

Derived from the test output `Initialize Migration` stage:

### SOURCE

| Field | Value | Source |
|-------|-------|--------|
| Database | MSSQL | `source.conf` |
| Host | localhost | `mssql.conf` |
| Port | 1533 | `mssql.conf` |
| DB | ecommerce_mssql | `mssql.conf` |
| Schema | dbo | `source.conf` |
| User | sa | `mssql.conf` |
| Password | ******** | `mssql.conf` |

### DESTINATION

| Field | Value | Source |
|-------|-------|--------|
| Database | MYSQL | `destination.conf` |
| Host | 127.0.0.1 | `mysql.conf` (or Jenkins param) |
| Port | 3306 | `mysql.conf` (or Jenkins param) |
| DB | test_schema_1 | Jenkins param override |
| Schema | (empty) | `destination.conf` |
| User | rootuser | `mysql.conf` (or Jenkins param) |
| Password | ******** | `mysql.conf` (or Jenkins param) |

`DESTINATION_DB` is `test_schema_1` rather than the configured default `ecommerce_mysql`, indicating a Jenkins parameter override.

## Stage-by-Stage Output

### Stage 1: Initialize Migration

**Script:** `scripts\batch\migration\windows\initialize_migration.bat`

Output:
```
SOURCE
-----------------------------------------------
Database : MSSQL
Host     : localhost
Port     : 1533
DB       : ecommerce_mssql
Schema   : dbo
User     : sa
Password : ************

DESTINATION
-----------------------------------------------
Database : MYSQL
Host     : 127.0.0.1
Port     : 3306
DB       : test_schema_1
Schema   :
User     : rootuser
Password : *******

MIGRATION INITIALIZATION: PASS
```

**Meaning:** Configuration resolved successfully. Source and destination are different endpoints.

---

### Stage 2: Validate Source

**Script:** `scripts\batch\migration\windows\validate_source.bat`

Output:
```
SOURCE VALIDATION
-----------------------------------------------
Database : MSSQL
Host     : localhost
Port     : 1533
DB       : ecommerce_mssql
Schema   : dbo
User     : sa
Password : ************
Connection: PASS
Database : PASS (verified: Ecommerce_MSSQL)
Schema   : PASS

SOURCE VALIDATION: PASS
```

**Meaning:**
- Connected to MSSQL successfully
- Database name verified as `Ecommerce_MSSQL` (case-insensitive match with `ecommerce_mssql`)
- Schema `dbo` exists in `sys.schemas`

---

### Stage 3: Validate Destination

**Script:** `scripts\batch\migration\windows\validate_destination.bat`

Output:
```
DESTINATION VALIDATION
-----------------------------------------------
Database : MYSQL
Host     : 127.0.0.1
Port     : 3306
DB       : test_schema_1
Schema   :
User     : rootuser
Password : *******
Database test_schema_1 does not exist
Creating database test_schema_1...
Database created successfully
Connection: PASS
Database : PASS (verified: test_schema_1)
Schema   : (none)

DESTINATION VALIDATION: PASS
```

**Meaning:**
- Database `test_schema_1` did not exist — it was auto-created
- After creation, connection and database verification passed
- MySQL schema is always reported as `(none)` because MySQL does not require schema validation

---

### Stage 4: Extract Source Schema

**Script:** `scripts\batch\migration\windows\extract_schema.bat`

Output (excerpt):
```
Source Database  : MSSQL
Target Metadata  : metadata/mysql/

Found 3 table(s) in source database
Extracted columns from customers: ['customer_id', 'customer_name', 'email', 'city', 'created_at', 'phone_number']
CDC Status [customers] : UNCHANGED
Extracted columns from products: ['product_id', 'product_name', 'category', 'price', 'stock_quantity']
CDC Status [products] : UNCHANGED
Extracted columns from orders: ['order_id', 'customer_id', 'order_date', 'total_amount', 'status']
CDC Status [orders] : UNCHANGED

Tables Extracted : 3
Table : customers
  - customer_id
  - customer_name
  - email
  - city
  - created_at
  - phone_number
Table : products
  - product_id
  - product_name
  - category
  - price
  - stock_quantity
Table : orders
  - order_id
  - customer_id
  - order_date
  - total_amount
  - status
Changed Tables   : 0
```

**Meaning:**
- Extracted 3 tables from MSSQL source
- All tables marked `UNCHANGED` (first extraction or no new columns since last run)
- No new columns detected — schema is stable
- Metadata written to `metadata/mysql/schema_registry.json` and `metadata/mysql/cdc_status.json`

---

### Stage 5: Generate Target DDL

**Script:** `scripts\batch\migration\windows\generate_ddl.bat`

Output (excerpt):
```
Destination Database : MYSQL

No schema changes detected. Nothing to generate.
Updated migration master.xml with 4 include(s)

Destination Database : MYSQL
Liquibase Directory   : C:\Users\Admin\.jenkins\workspace\001_mig_shema_extrat\liquibase\migration\mysql

Generated Files      : 3
  - 001_create_customers.xml
  - 002_create_orders.xml
  - 003_create_products.xml

GENERATE TARGET DDL: PASS
```

**Meaning:**
- No schema changes detected compared to existing changelog files (idempotent behavior)
- `master.xml` updated with 4 includes (3 table creation files + `master_objects.xml`)
- 3 changelog files generated for the 3 tables

---

### Stage 6: Install Liquibase

**Script:** `scripts\batch\common\install_liquibase.bat`

Output:
```
Liquibase already exists.

LIQUIBASE INSTALLATION SUCCESSFUL
```

**Meaning:** Liquibase was already installed in the workspace. No download needed.

---

### Stage 7: Install Drivers

Three scripts ran sequentially:

| Script | Output |
|--------|--------|
| `install_mssql_driver.bat` | `MSSQL JDBC Driver already exists.` |
| `install_mysql_driver.bat` | `MySQL Connector already installed.` |
| `install_postgresql_driver.bat` | `PostgreSQL JDBC Driver already installed.` |

**Meaning:** All required JDBC drivers were already present.

---

### Stage 8: Apply Schema

**Script:** `scripts\batch\migration\windows\apply_schema.bat`

Output (excerpt):
```
Destination Database : MYSQL

RUNNING MIGRATION LIQUIBASE
========================================

Selected Version : JDK 21
JAVA_HOME         : C:\Program Files\Eclipse Adoptium\jdk-21.0.11.10-hotspot

Expected Liquibase Version : 5.0.3

Liquibase Version: 5.0.3

VALIDATING MYSQL JDBC DRIVER
========================================
Driver Found:
C:\Users\Admin\.jenkins\workspace\001_mig_shema_extrat\tools\drivers\mysql-connector-j-9.5.0.jar

UPDATE SUMMARY
Run:                          3
Previously run:               0
Filtered out:                 0
-------------------------------
Total change sets:            3

MYSQL LIQUIBASE update COMPLETED

Running Changeset: liquibase/migration/mysql/001_create_customers.xml::001::tanisha
Running Changeset: liquibase/migration/mysql/002_create_orders.xml::002::tanisha
Running Changeset: liquibase/migration/mysql/003_create_products.xml::003::tanisha
Liquibase: Update has been successful. Rows affected: 0
Liquibase command 'update' was executed successfully.

APPLY SCHEMA: PASS
```

**Meaning:**
- JDK 21 validated successfully
- Liquibase 5.0.3 validated
- MySQL driver `mysql-connector-j-9.5.0.jar` validated
- All 3 changesets executed successfully against MySQL
- No rows affected (expected for DDL-only migration)
- Destination database `test_schema_1` now contains the 3 tables: `customers`, `orders`, `products`

---

## Final Result

```
Finished: SUCCESS
```

The MSSQL → MySQL migration completed successfully, creating `test_schema_1` with 3 tables matching the source schema.
