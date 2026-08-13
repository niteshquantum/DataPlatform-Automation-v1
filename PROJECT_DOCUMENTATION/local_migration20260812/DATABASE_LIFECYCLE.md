# Database Lifecycle — Windows Migration Pipeline

## Destination Database Handling

The pipeline supports two cases for the destination database.

---

### CASE A — Destination Database Already Exists

```
Check DB
   ↓
Exists
   ↓
Connect
   ↓
Validate
   ↓
Continue
```

1. Resolve effective destination configuration.
2. Check whether the database exists using a bootstrap/server-level connection.
3. If it exists, do **NOT** create it again.
4. Connect to the destination database.
5. Validate connection.
6. Validate database.
7. Validate schema if applicable.
8. Continue migration.

---

### CASE B — Destination Database Does NOT Exist

```
Check DB
   ↓
Does NOT exist
   ↓
Bootstrap connection
   ↓
CREATE DATABASE
   ↓
Reconnect
   ↓
Validate
   ↓
Continue
```

1. Resolve effective destination configuration.
2. Check database existence using a bootstrap/server-level connection.
3. Database is missing.
4. Create database.
5. Reconnect to the newly created database.
6. Validate database.
7. Validate schema if applicable.
8. Continue migration.

---

## Database-Specific Bootstrap Behavior

| Database | Bootstrap Connection | Create Statement | Notes |
|----------|---------------------|------------------|-------|
| **MySQL** | Connect to server **without** selecting the destination database | `CREATE DATABASE \`<db_name>\`` | Followed by `conn.commit()` |
| **PostgreSQL** | Use the `postgres` database for bootstrap connection | `CREATE DATABASE "<db_name>"` | `CREATE DATABASE` requires autocommit / cannot run inside a transaction |
| **MSSQL** | Use `master` for bootstrap connection | `CREATE DATABASE [<db_name>]` | `conn.autocommit = True` is set before execution |

---

## Safety Rule

**The migration pipeline must NEVER automatically DROP an existing destination database.**

This behavior was introduced because earlier testing failed when the destination database did not exist.

---

## Testing Examples

Observed destination databases during local testing:

| Database | Example Name |
|----------|-------------|
| PostgreSQL | `test_db_postgre` |
| MySQL | `test_db` / `test_db_mysql` |
| MSSQL | `test_db_mssql` |
